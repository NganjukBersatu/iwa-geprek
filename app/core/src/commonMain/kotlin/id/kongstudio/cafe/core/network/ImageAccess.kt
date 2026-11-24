package id.kongstudio.cafe.core.network

import io.ktor.client.HttpClient
import io.ktor.client.plugins.api.createClientPlugin
import io.ktor.client.request.bearerAuth
import io.ktor.http.Url
import kotlinx.coroutines.flow.MutableStateFlow

/** Token yang menyertai pemuatan gambar dari server sendiri; kosong berarti belum ada yang masuk. */
class ImageAccess {
    private val token = MutableStateFlow<String?>(null)

    val current: String? get() = token.value

    fun use(value: String?) {
        token.value = value
    }
}

private const val STATIC_PATH = "/static/"

/** Klien pemuat gambar: token hanya dikirim ke alamat server sendiri, tidak ke situs lain yang gambarnya ikut tampil. */
fun createImageClient(apiBaseUrl: String, access: ImageAccess): HttpClient {
    val api = Url(apiBaseUrl)
    val apiHost = api.host
    val plugin = createClientPlugin("ImageAccess") {
        onRequest { request, _ ->
            // Alamat berkas dibuat server dari alamat publiknya, yang bisa berbeda dari alamat yang dipakai perangkat ini (IP LAN, tunnel); berkas server sendiri selalu dimuat lewat alamat API supaya token ikut terkirim.
            if (request.url.host != apiHost && request.url.build().encodedPath.startsWith(STATIC_PATH)) {
                request.url.protocol = api.protocol
                request.url.host = api.host
                request.url.port = api.port
            }
            val token = access.current
            if (token != null && request.url.host == apiHost) request.bearerAuth(token)
        }
    }
    return HttpClient { install(plugin) }
}
