package id.kongstudio.cafe.feature.operational

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.feature.devicesetup.deviceCall
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.plugins.sse.SSEClientException
import io.ktor.client.plugins.sse.sse
import io.ktor.client.plugins.timeout
import io.ktor.client.request.bearerAuth
import io.ktor.http.HttpMethod
import io.ktor.http.HttpStatusCode
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withTimeoutOrNull
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

private const val StatusLinked = "terhubung"
private const val StatusWaiting = "menunggu"
private const val EventStatus = "status"
private const val RetryDelayMillis = 5_000L
private const val TickMillis = 1_000L
private const val InfiniteMillis = Long.MAX_VALUE
// Server mengirim detak tiap 3 detik; sunyi selama ini berarti sambungan mati diam-diam.
private const val SilenceMillis = 10_000L
// Tanpa pemindaian selama ini QR ditutup, supaya tablet yang ditinggal tidak terus menayangkannya.
private const val IdleMillis = 60_000L

private val QrJson = Json { ignoreUnknownKeys = true }

internal data class OperationalUiState(
    /** Isi QR yang sedang tampil; null sampai server menerbitkannya. */
    val token: String? = null,
    val secondsLeft: Int = 0,
    /** Sebab terakhir gagal (null bila lancar), ditampilkan apa adanya. */
    val failure: AppFailure? = null,
    /** Sudah ada karyawan yang memindai QR; layar berpindah ke dashboard. */
    val connected: Boolean = false,
    /** QR ditutup karena tidak ada pemindaian; tampil lagi lewat tombol. */
    val closed: Boolean = false,
    val userName: String? = null,
    /** JWT karyawan yang memindai; null bila server tidak memberikannya (jendela terlewat). */
    val userToken: String? = null,
)

/** Meminta QR ke server, menampilkannya sampai habis, memantau pemindaian, lalu meminta yang baru; berhenti begitu terhubung, perangkat tidak dikenal, atau tidak ada pemindaian selama [IdleMillis]. */
internal class OperationalViewModel(
    private val client: HttpClient,
    private val baseUrl: String,
    private val deviceToken: String,
    private val onRevoked: () -> Unit,
    private val onLinked: (userName: String?, userToken: String?) -> Unit,
    alreadyLinked: Boolean,
) : ViewModel() {
    private val _state = MutableStateFlow(OperationalUiState(connected = alreadyLinked))
    val state: StateFlow<OperationalUiState> = _state.asStateFlow()

    private var job: Job? = null

    init {
        if (!alreadyLinked) start()
    }

    fun showQr() {
        if (job?.isActive == true) return
        _state.update { it.copy(closed = false, token = null, failure = null) }
        start()
    }

    private fun start() {
        job = viewModelScope.launch {
            if (withTimeoutOrNull(IdleMillis) { run() } == null) _state.update { it.copy(closed = true, token = null) }
        }
    }

    private suspend fun run() {
        while (true) {
            val issued = deviceCall(
                client = client,
                baseUrl = baseUrl,
                method = HttpMethod.Post,
                path = "/v2/devices/qr",
                bearer = deviceToken,
                parse = { it.body<QrDto>() },
            )
            when (issued) {
                is DeviceResult.Ok -> if (watch(issued.value)) return
                is DeviceResult.Failed -> {
                    if (issued.failure == AppFailure.Unauthorized) {
                        onRevoked()
                        return
                    }
                    _state.update { it.copy(failure = issued.failure) }
                    delay(RetryDelayMillis)
                }
            }
        }
    }

    /** Mengembalikan true bila loop utama harus berhenti (terhubung atau perangkat dicabut). */
    private suspend fun watch(qr: QrDto): Boolean = coroutineScope {
        _state.update { it.copy(token = qr.token, secondsLeft = qr.validSeconds, failure = null) }
        val countdown = launch {
            for (left in qr.validSeconds - 1 downTo 0) {
                delay(TickMillis)
                _state.update { it.copy(secondsLeft = left) }
            }
        }
        val linked = listen(qr)
        countdown.cancel()
        linked
    }

    /** Menunggu kabar QR lewat SSE sampai dipindai atau kedaluwarsa; sambungan yang putus disambung lagi selama QR masih berlaku. */
    private suspend fun listen(qr: QrDto): Boolean {
        while (_state.value.secondsLeft > 0) {
            var outcome: QrStatusDto? = null
            try {
                client.sse(
                    urlString = "${baseUrl.trimEnd('/')}/v2/devices/qr/${qr.id}/stream",
                    request = {
                        bearerAuth(deviceToken)
                        timeout {
                            requestTimeoutMillis = InfiniteMillis
                            socketTimeoutMillis = SilenceMillis
                        }
                    },
                ) {
                    incoming.collect { frame ->
                        if (frame.event != EventStatus) return@collect
                        val body = frame.data ?: return@collect
                        val status = runCatching { QrJson.decodeFromString(QrStatusDto.serializer(), body) }.getOrNull()
                        if (status != null && status.status != StatusWaiting) outcome = status
                    }
                }
            } catch (e: CancellationException) {
                throw e
            } catch (e: SSEClientException) {
                if (e.response?.status == HttpStatusCode.Unauthorized) {
                    onRevoked()
                    return true
                }
            } catch (e: Exception) {
                // Putus: disambung lagi di putaran berikutnya selama QR masih berlaku.
            }
            val status = outcome
            if (status?.status == StatusLinked) {
                onLinked(status.userName, status.accessToken)
                _state.update { it.copy(connected = true, userName = status.userName, userToken = status.accessToken) }
                return true
            }
            if (status != null) return false
            delay(TickMillis)
        }
        return false
    }
}

@Serializable
private class QrDto(
    val id: String,
    val token: String,
    @SerialName("valid_seconds") val validSeconds: Int,
)

@Serializable
private class QrStatusDto(
    val status: String,
    @SerialName("user_name") val userName: String? = null,
    @SerialName("access_token") val accessToken: String? = null,
)
