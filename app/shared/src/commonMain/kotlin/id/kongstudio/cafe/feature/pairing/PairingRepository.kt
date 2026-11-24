package id.kongstudio.cafe.feature.pairing

import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.feature.devicesetup.deviceCall
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.HttpMethod
import io.ktor.http.contentType
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/** Perangkat operasional yang baru ditautkan. */
internal class LinkedDevice(val name: String)

internal interface PairingRepository {
    suspend fun link(qrToken: String): DeviceResult<LinkedDevice>
}

internal class KtorPairingRepository(
    private val client: HttpClient,
    private val baseUrl: String,
    private val accessToken: String,
) : PairingRepository {

    override suspend fun link(qrToken: String): DeviceResult<LinkedDevice> =
        deviceCall(
            client = client,
            baseUrl = baseUrl,
            method = HttpMethod.Post,
            path = "/v2/devices/link",
            bearer = accessToken,
            configure = {
                contentType(ContentType.Application.Json)
                setBody(LinkRequestDto(qrToken))
            },
            parse = { LinkedDevice(it.body<LinkResponseDto>().deviceName) },
        )
}

@Serializable
private class LinkRequestDto(val token: String)

@Serializable
private class LinkResponseDto(@SerialName("device_name") val deviceName: String)
