package id.kongstudio.cafe.feature.mysession

import id.kongstudio.cafe.feature.sessions.SessionItem
import id.kongstudio.cafe.feature.sessions.SessionOrder
import id.kongstudio.cafe.feature.sessions.SessionRepository
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.feature.admin.PageRequest
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

private const val RecentCount = 7

internal data class MySessionState(
    val loading: Boolean = true,
    val failure: AppFailure? = null,
    /** Sesi yang sedang berjalan milik karyawan ini; null bila belum dibuka. */
    val running: SessionItem? = null,
    /** Sesi terakhir yang sudah ditutup. */
    val last: SessionItem? = null,
    /** Sesi terbaru urut dari yang paling lama, untuk grafik. */
    val recent: List<SessionItem> = emptyList(),
    /** Rincian metode bayar per UUID sesi, untuk sesi berjalan dan sesi terakhir. */
    val methods: Map<String, MethodsState> = emptyMap(),
)

/** Sesi yang dibuka di lembar rincian beserta pesanannya; [orders] null selama belum terbaca. */
internal data class SessionDetailState(
    val session: SessionItem,
    val orders: List<SessionOrder>? = null,
    val failure: AppFailure? = null,
)

/** Sesi berjalan, sesi terakhir, dan rincian satu sesi milik karyawan yang memegang tablet, dibaca dari backend v2. */
internal class MySessionViewModel(
    private val repository: SessionRepository,
    private val onUnauthorized: () -> Unit,
) : ViewModel() {
    private val _state = MutableStateFlow(MySessionState())
    val state: StateFlow<MySessionState> = _state.asStateFlow()
    private val _detail = MutableStateFlow<SessionDetailState?>(null)
    val detail: StateFlow<SessionDetailState?> = _detail.asStateFlow()
    private var ordersJob: Job? = null

    /** Kerangka hanya tampil pada muatan pertama; sesudahnya angka diganti tanpa berkedip. */
    fun refresh() {
        val first = _state.value.let { it.running == null && it.last == null }
        if (first) _state.update { it.copy(loading = true, failure = null) }
        viewModelScope.launch {
            val request = PageRequest(page = 0, query = "", filter = "", params = emptyMap())
            when (val result = repository.list(request, size = RecentCount)) {
                is DeviceResult.Ok -> {
                    val items = result.value.items
                    val running = items.firstOrNull { item -> item.open }
                    val last = items.firstOrNull { item -> !item.open }
                    _state.update {
                        it.copy(loading = false, failure = null, running = running, last = last, recent = items.reversed())
                    }
                    listOfNotNull(running, last).filter { it.revenue > 0 }.forEach { loadMethods(it.id) }
                }
                is DeviceResult.Failed -> {
                    if (result.failure == AppFailure.Unauthorized) onUnauthorized()
                    _state.update { it.copy(loading = false, failure = result.failure) }
                }
            }
        }
    }

    // Rincian yang sudah tampil tidak diganti kerangka saat dimuat ulang; gagal dibaca hanya menyembunyikan donat metode.
    private suspend fun loadMethods(sessionId: String) {
        if (_state.value.methods[sessionId] == null) _state.update { it.copy(methods = it.methods + (sessionId to MethodsState.Loading)) }
        val next = when (val result = repository.methods(sessionId)) {
            is DeviceResult.Ok -> MethodsState.Ready(result.value)
            is DeviceResult.Failed -> {
                if (result.failure == AppFailure.Unauthorized) onUnauthorized()
                _state.value.methods[sessionId] as? MethodsState.Ready ?: MethodsState.Failed
            }
        }
        _state.update { it.copy(methods = it.methods + (sessionId to next)) }
    }

    fun openDetail(session: SessionItem) {
        _detail.value = SessionDetailState(session)
        loadOrders(session)
    }

    fun retryOrders() {
        _detail.value?.let { current ->
            _detail.value = current.copy(orders = null, failure = null)
            loadOrders(current.session)
        }
    }

    fun closeDetail() {
        ordersJob?.cancel()
        _detail.value = null
    }

    private fun loadOrders(session: SessionItem) {
        ordersJob?.cancel()
        ordersJob = viewModelScope.launch {
            when (val result = repository.orders(session.id)) {
                is DeviceResult.Ok -> _detail.update { it?.copy(orders = result.value, failure = null) }
                is DeviceResult.Failed -> {
                    if (result.failure == AppFailure.Unauthorized) onUnauthorized()
                    _detail.update { it?.copy(failure = result.failure) }
                }
            }
        }
    }
}
