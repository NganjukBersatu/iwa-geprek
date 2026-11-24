package id.kongstudio.cafe.feature.auth.session

import io.ktor.client.HttpClient
import io.ktor.client.request.bearerAuth
import io.ktor.client.request.post
import io.ktor.http.HttpStatusCode
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

private const val LogoutPath = "/v2/auth/logout"

/** Satu pintu keluar: token dicabut di server, dan yang gagal karena offline disimpan lalu dikirim ulang lewat [flush]. */
class SessionRevoker(
    private val client: HttpClient,
    baseUrl: String,
    private val store: SessionStore,
) {
    private val url = baseUrl.trimEnd('/') + LogoutPath
    private val mutex = Mutex()

    /** Token disimpan dulu sebelum dikirim, jadi app yang tertutup di tengah jalan tetap mencabutnya nanti. */
    suspend fun revoke(token: String) {
        store.addPendingRevocation(token)
        flush()
    }

    suspend fun flush() {
        mutex.withLock {
            for (token in store.pendingRevocations()) {
                if (!send(token)) return
                store.removePendingRevocation(token)
            }
        }
    }

    /** Benar bila server sudah tidak menerima token itu, termasuk yang sudah dicabut, kedaluwarsa, atau akunnya nonaktif. */
    private suspend fun send(token: String): Boolean = try {
        val status = client.post(url) { bearerAuth(token) }.status
        status.value in 200..299 || status == HttpStatusCode.Unauthorized || status == HttpStatusCode.Forbidden
    } catch (e: CancellationException) {
        throw e
    } catch (e: Exception) {
        false
    }
}
