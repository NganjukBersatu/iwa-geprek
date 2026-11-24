package id.kongstudio.cafe.feature.admin

import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.feature.devicesetup.deviceCall
import id.kongstudio.cafe.feature.sessions.DeviceHeader
import io.ktor.client.HttpClient
import io.ktor.client.plugins.timeout
import io.ktor.client.request.forms.MultiPartFormDataContent
import io.ktor.client.request.forms.formData
import io.ktor.client.request.HttpRequestBuilder
import io.ktor.client.request.header
import io.ktor.client.request.parameter
import io.ktor.client.request.setBody
import io.ktor.client.statement.bodyAsText
import io.ktor.http.ContentType
import io.ktor.http.Headers
import io.ktor.http.HttpHeaders
import io.ktor.http.HttpMethod
import io.ktor.http.content.TextContent
import kotlinx.serialization.DeserializationStrategy
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement

private const val UploadTimeoutMillis = 60_000L

internal val AdminJson = Json {
    ignoreUnknownKeys = true
    isLenient = true
}

/** Panggilan layar kelola atas nama karyawan pemegang tablet, dengan isian tulis berupa JSON dari pemanggil supaya PATCH hanya memuat yang berubah; [deviceToken] membuat server memakai cabang tablet. */
internal class AdminApi(
    private val client: HttpClient,
    private val baseUrl: String,
    private val token: String,
    private val deviceToken: String? = null,
) {
    private fun HttpRequestBuilder.fromDevice() {
        deviceToken?.let { header(DeviceHeader, it) }
    }

    suspend fun <T> get(
        path: String,
        serializer: DeserializationStrategy<T>,
        query: Map<String, Any?> = emptyMap(),
    ): DeviceResult<T> = deviceCall(
        client = client,
        baseUrl = baseUrl,
        method = HttpMethod.Get,
        path = path,
        bearer = token,
        configure = {
            fromDevice()
            query.forEach { (key, value) ->
                // Daftar dikirim sebagai kunci yang berulang (kind=a&kind=b), bukan teks "[a, b]".
                val values = if (value is Iterable<*>) value.toList() else listOf(value)
                values.forEach { one -> if (one != null && one.toString().isNotBlank()) parameter(key, one) }
            }
        },
        parse = { AdminJson.decodeFromString(serializer, it.bodyAsText()) },
    )

    suspend fun <T> send(
        method: HttpMethod,
        path: String,
        body: JsonElement?,
        serializer: DeserializationStrategy<T>,
    ): DeviceResult<T> = deviceCall(
        client = client,
        baseUrl = baseUrl,
        method = method,
        path = path,
        bearer = token,
        configure = {
            fromDevice()
            body?.let { setBody(TextContent(it.toString(), ContentType.Application.Json)) }
        },
        parse = { AdminJson.decodeFromString(serializer, it.bodyAsText()) },
    )

    /** Untuk jawaban yang isinya tidak dipakai (hapus, aktifkan). */
    suspend fun sendUnit(method: HttpMethod, path: String, body: JsonElement? = null): DeviceResult<Unit> =
        deviceCall(
            client = client,
            baseUrl = baseUrl,
            method = method,
            path = path,
            bearer = token,
            configure = {
            fromDevice()
            body?.let { setBody(TextContent(it.toString(), ContentType.Application.Json)) }
        },
            parse = { },
        )

    /** Mengunggah satu gambar JPEG sebagai bidang [field] (boleh tanpa gambar) bersama bidang teks [fields], lalu membaca jawabannya. */
    suspend fun <T> upload(
        path: String,
        field: String,
        bytes: ByteArray?,
        serializer: DeserializationStrategy<T>,
        method: HttpMethod = HttpMethod.Post,
        fields: Map<String, String> = emptyMap(),
    ): DeviceResult<T> = deviceCall(
        client = client,
        baseUrl = baseUrl,
        method = method,
        path = path,
        bearer = token,
        configure = {
            fromDevice()
            timeout { requestTimeoutMillis = UploadTimeoutMillis }
            setBody(
                MultiPartFormDataContent(
                    formData {
                        fields.forEach { (key, value) -> append(key, value) }
                        if (bytes != null) {
                            append(
                                field,
                                bytes,
                                Headers.build {
                                    append(HttpHeaders.ContentType, "image/jpeg")
                                    append(HttpHeaders.ContentDisposition, "filename=\"foto.jpg\"")
                                },
                            )
                        }
                    },
                ),
            )
        },
        parse = { AdminJson.decodeFromString(serializer, it.bodyAsText()) },
    )
}
