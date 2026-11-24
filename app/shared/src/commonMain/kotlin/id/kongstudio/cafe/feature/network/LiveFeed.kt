package id.kongstudio.cafe.feature.network

import io.ktor.client.HttpClient
import io.ktor.client.plugins.sse.SSEClientException
import io.ktor.client.plugins.sse.sse
import io.ktor.client.plugins.timeout
import io.ktor.client.request.bearerAuth
import io.ktor.http.HttpStatusCode
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.filter
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

private const val StreamPath = "/v2/live"
private const val InfiniteMillis = Long.MAX_VALUE
// Server mengirim detak tiap 3 detik; sunyi selama ini berarti sambungan mati diam-diam.
private const val SilenceMillis = 10_000L
private const val FirstRetryMillis = 1_000L
private const val MaxRetryMillis = 15_000L
private const val EventResync = "resync"
private const val EventChange = "ubah"
private const val BufferedChanges = 64

private val LiveJson = Json { ignoreUnknownKeys = true }

@Serializable
private class ChangeDto(val tables: List<String> = emptyList())

/** Satu sinyal dari server: tabel yang berubah, atau [resync] bila layar harus mengambil ulang semuanya. */
class LiveChange(val tables: Set<String>, val resync: Boolean) {
    fun touches(watched: Set<String>): Boolean = resync || tables.any { it in watched }
}

/** Saluran realtime /v2/live untuk satu karyawan: satu sambungan dibagi semua layar, tersambung ulang sendiri, tanpa polling. */
class LiveFeed(
    private val client: HttpClient,
    baseUrl: String,
    private val token: String,
    private val onUnauthorized: () -> Unit,
) {
    private val url = "${baseUrl.trimEnd('/')}$StreamPath"
    private val _changes = MutableSharedFlow<LiveChange>(extraBufferCapacity = BufferedChanges)
    private val _connected = MutableStateFlow(false)

    val changes: SharedFlow<LiveChange> = _changes.asSharedFlow()
    val connected: StateFlow<Boolean> = _connected.asStateFlow()

    /** Sinyal untuk layar yang membaca [tables]; sambungan baru selalu ikut, sebagai pengejar yang terlewat. */
    fun of(tables: Set<String>): Flow<LiveChange> = changes.filter { it.touches(tables) }

    /** Berjalan sampai dibatalkan; menyambung saat internet ada dan berhenti saat hilang. */
    suspend fun run(online: StateFlow<Boolean>) {
        online.collectLatest { reachable ->
            if (reachable) listen() else _connected.value = false
        }
    }

    private suspend fun listen() {
        var retry = FirstRetryMillis
        while (true) {
            try {
                client.sse(
                    urlString = url,
                    request = {
                        bearerAuth(token)
                        timeout {
                            requestTimeoutMillis = InfiniteMillis
                            socketTimeoutMillis = SilenceMillis
                        }
                    },
                ) {
                    incoming.collect { frame ->
                        when (frame.event) {
                            EventResync -> {
                                retry = FirstRetryMillis
                                _connected.value = true
                                _changes.emit(LiveChange(emptySet(), resync = true))
                            }
                            EventChange -> {
                                val body = frame.data ?: return@collect
                                val change = runCatching { LiveJson.decodeFromString(ChangeDto.serializer(), body) }.getOrNull()
                                    ?: return@collect
                                _changes.emit(LiveChange(change.tables.toSet(), resync = false))
                            }
                        }
                    }
                }
            } catch (e: CancellationException) {
                throw e
            } catch (e: SSEClientException) {
                if (e.response?.status == HttpStatusCode.Unauthorized) {
                    _connected.value = false
                    onUnauthorized()
                    return
                }
            } catch (e: Exception) {
                // Putus: jatuh ke jeda lalu sambung ulang; layar mengejar lewat resync.
            }
            _connected.value = false
            delay(retry)
            retry = (retry * 2).coerceAtMost(MaxRetryMillis)
        }
    }
}
