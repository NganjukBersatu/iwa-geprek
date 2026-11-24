package id.kongstudio.cafe.core.network

import io.ktor.client.HttpClient
import io.ktor.client.plugins.HttpResponseValidator
import io.ktor.client.plugins.HttpTimeout
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.plugins.defaultRequest
import io.ktor.client.plugins.sse.SSE
import io.ktor.client.request.header
import io.ktor.serialization.kotlinx.json.json
import kotlinx.serialization.json.Json

private const val ClientHeader = "X-App-Client"
private const val VersionHeader = "X-App-Version"
private const val ClientName = "apk"
private const val UpgradeRequired = 426

/** Setiap permintaan menyebut nama dan [appVersion] aplikasi; jawaban 426 (versi sudah tidak didukung) diteruskan ke [onUpgradeRequired]. */
fun createApiClient(appVersion: String, onUpgradeRequired: () -> Unit): HttpClient = HttpClient {
    install(ContentNegotiation) {
        json(Json { ignoreUnknownKeys = true })
    }
    install(SSE)
    install(HttpTimeout) {
        connectTimeoutMillis = 15_000
        requestTimeoutMillis = 30_000
    }
    defaultRequest {
        header(ClientHeader, ClientName)
        header(VersionHeader, appVersion)
    }
    HttpResponseValidator {
        validateResponse { response -> if (response.status.value == UpgradeRequired) onUpgradeRequired() }
    }
}
