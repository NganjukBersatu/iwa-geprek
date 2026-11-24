package id.kongstudio.cafe.feature.ordersync

import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.feature.devicesetup.deviceCall
import id.kongstudio.cafe.feature.sessions.DeviceHeader
import id.kongstudio.cafe.offline.OfflineStore
import id.kongstudio.cafe.offline.userIdOf
import io.ktor.client.HttpClient
import io.ktor.http.ContentType
import io.ktor.http.HttpMethod
import io.ktor.http.content.TextContent
import io.ktor.client.request.header
import io.ktor.client.request.setBody
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

internal const val OrdersPath = "/v2/operational/orders"

internal sealed interface FlushOutcome {
    /** Antrean milik karyawan ini sudah habis diproses atau tidak ada yang bisa dikirim. */
    data object Done : FlushOutcome

    /** Berhenti di tengah jalan karena server tidak terjangkau atau sedang galat; sisanya tetap antre. */
    data object Retry : FlushOutcome

    /** Token karyawan ditolak; pesanannya tertahan sampai karyawan itu memindai QR lagi. */
    data object LoginRequired : FlushOutcome
}

/** Mengirim antrean pesanan karyawan pemegang tablet berurutan menurut waktu dibuat, dengan yang ditolak server ditandai dan dilewati, tidak pernah dihapus atau dikirim ulang diam-diam. */
internal class OrderSyncer(
    private val client: HttpClient,
    private val baseUrl: String,
    private val token: String,
    private val deviceToken: String,
    private val store: OfflineStore,
) {
    private val userId = userIdOf(token)
    private val lock = Mutex()

    suspend fun flush(): FlushOutcome = lock.withLock {
        val owner = userId ?: return@withLock FlushOutcome.Done
        store.requeueNeedsLogin(owner)

        for (entry in store.queuedFor(owner)) {
            val result = deviceCall(
                client = client,
                baseUrl = baseUrl,
                method = HttpMethod.Post,
                path = OrdersPath,
                bearer = token,
                configure = {
                    header(DeviceHeader, deviceToken)
                    setBody(TextContent(entry.payload, ContentType.Application.Json))
                },
                parse = { },
            )
            when (result) {
                is DeviceResult.Ok -> store.delete(entry.clientId)
                is DeviceResult.Failed -> when (val failure = result.failure) {
                    is AppFailure.Unreachable, is AppFailure.Timeout, is AppFailure.SecureConnection,
                    is AppFailure.Unexpected, is AppFailure.Server,
                    -> {
                        store.markAttempt(entry.clientId)
                        return@withLock FlushOutcome.Retry
                    }
                    AppFailure.Unauthorized -> {
                        store.markNeedsLogin(entry.clientId)
                        return@withLock FlushOutcome.LoginRequired
                    }
                    is AppFailure.Rejected -> store.markRejected(entry.clientId, failure.message)
                    is AppFailure.NotFound -> store.markRejected(entry.clientId, null)
                }
            }
        }
        FlushOutcome.Done
    }
}
