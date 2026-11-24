package id.kongstudio.cafe.feature.devicesetup

import id.kongstudio.cafe.core.failure.AppFailure
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.HttpMethod
import io.ktor.http.contentType
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

sealed interface DevicePairingResult {
    data class Paired(val credential: DeviceCredential) : DevicePairingResult

    data class Failed(val failure: AppFailure) : DevicePairingResult
}

interface DevicePairingRepository {
    suspend fun pair(code: String, info: DeviceInfo): DevicePairingResult
}

class KtorDevicePairingRepository(
    private val client: HttpClient,
    private val baseUrl: String,
) : DevicePairingRepository {

    override suspend fun pair(code: String, info: DeviceInfo): DevicePairingResult {
        val result = deviceCall(
            client = client,
            baseUrl = baseUrl,
            method = HttpMethod.Post,
            path = "/v2/devices/pair",
            configure = {
                contentType(ContentType.Application.Json)
                setBody(PairingRequestDto(code, info.androidId, info.serial, info.brand, info.model))
            },
            parse = { response ->
                val dto = response.body<PairingResponseDto>()
                DeviceCredential(dto.id, dto.token, dto.name, dto.section)
            },
        )
        return when (result) {
            is DeviceResult.Ok -> DevicePairingResult.Paired(result.value)
            is DeviceResult.Failed -> DevicePairingResult.Failed(result.failure)
        }
    }
}

@Serializable
private class PairingRequestDto(
    val code: String,
    @SerialName("android_id") val androidId: String?,
    val serial: String?,
    val brand: String?,
    val model: String?,
)

@Serializable
private class PairingResponseDto(
    val id: String,
    val token: String,
    val name: String,
    val section: String,
)
