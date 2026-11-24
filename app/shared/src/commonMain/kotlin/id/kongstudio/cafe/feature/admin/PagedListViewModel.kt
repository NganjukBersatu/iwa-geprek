package id.kongstudio.cafe.feature.admin

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.feature.network.LiveChange
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

private const val SearchDebounceMillis = 350L

internal class ListPage<T>(val items: List<T>, val total: Int)

/** Satu permintaan halaman; [page] berbasis nol, [params] untuk penyaring tambahan seperti rentang tanggal. */
internal class PageRequest(
    val page: Int,
    val query: String,
    val filter: String,
    val params: Map<String, String>,
    /** Urutan yang dipilih layar, misalnya "-time"; kosong memakai urutan bawaan server. */
    val sort: String = "",
)

internal data class PagedState<T>(
    val items: List<T> = emptyList(),
    val total: Int = 0,
    /** Halaman berbasis nol. */
    val page: Int = 0,
    val query: String = "",
    val filter: String = "",
    val params: Map<String, String> = emptyMap(),
    val sort: String = "",
    val loading: Boolean = true,
    val failure: AppFailure? = null,
    /** Sedang menjalankan tindakan tulis (simpan, hapus, aktifkan). */
    val acting: Boolean = false,
    val actionFailure: AppFailure? = null,
)

/** Daftar berhalaman dengan pencarian dan penyaring untuk semua layar kelola, dengan tindakan tulis lewat [act] supaya status sibuk dan galatnya seragam. */
internal class PagedListViewModel<T>(
    val pageSize: Int,
    private val loader: suspend (PageRequest) -> DeviceResult<ListPage<T>>,
    private val onUnauthorized: () -> Unit,
    initialFilter: String = "",
    initialParams: Map<String, String> = emptyMap(),
    initialSort: String = "",
    /** Sinyal live yang membuat daftar dimuat ulang; kosong berarti daftar tidak mendengarkan. */
    changes: Flow<LiveChange>? = null,
) : ViewModel() {
    private val _state = MutableStateFlow(PagedState<T>(filter = initialFilter, params = initialParams, sort = initialSort))
    val state: StateFlow<PagedState<T>> = _state.asStateFlow()
    private var loadJob: Job? = null
    private var searchJob: Job? = null

    init {
        reload()
        changes?.let { feed -> viewModelScope.launch { feed.collect { reload(quiet = true) } } }
    }

    val pageCount: Int get() = ((_state.value.total + pageSize - 1) / pageSize).coerceAtLeast(1)

    fun setQuery(value: String) {
        _state.update { it.copy(query = value) }
        searchJob?.cancel()
        searchJob = viewModelScope.launch {
            delay(SearchDebounceMillis)
            _state.update { it.copy(page = 0) }
            reload()
        }
    }

    /** Pindah penyaring bisa sekaligus pindah urutan, dengan satu kali muat ulang. */
    fun setFilter(value: String, sort: String? = null) {
        if (value == _state.value.filter) return
        _state.update { it.copy(filter = value, page = 0, sort = sort ?: it.sort) }
        reload()
    }

    fun setSort(value: String) {
        if (value == _state.value.sort) return
        _state.update { it.copy(sort = value, page = 0) }
        reload()
    }

    fun setParams(vararg changes: Pair<String, String>) {
        _state.update { it.copy(params = it.params + changes, page = 0) }
        reload()
    }

    fun setPage(page: Int) {
        _state.update { it.copy(page = page.coerceIn(0, pageCount - 1)) }
        reload()
    }

    /** [quiet] dipakai sinyal live: daftar yang sudah tampil tidak diganti kerangka pemuatan. */
    fun reload(quiet: Boolean = false) {
        loadJob?.cancel()
        _state.update { it.copy(loading = !quiet || it.items.isEmpty(), failure = null) }
        val current = _state.value
        loadJob = viewModelScope.launch {
            val request = PageRequest(current.page, current.query.trim(), current.filter, current.params, current.sort)
            when (val result = loader(request)) {
                is DeviceResult.Ok -> {
                    val lastPage = ((result.value.total + pageSize - 1) / pageSize - 1).coerceAtLeast(0)
                    if (current.page > lastPage) {
                        // Halaman terakhir kosong setelah data berkurang: mundur ke halaman terakhir yang ada.
                        _state.update { it.copy(page = lastPage) }
                        reload(quiet)
                    } else {
                        _state.update { it.copy(items = result.value.items, total = result.value.total, loading = false) }
                    }
                }
                is DeviceResult.Failed -> {
                    if (result.failure == AppFailure.Unauthorized) {
                        onUnauthorized()
                    } else {
                        _state.update { it.copy(loading = false, failure = result.failure) }
                    }
                }
            }
        }
    }

    fun clearActionFailure() = _state.update { it.copy(actionFailure = null) }

    /** Menjalankan satu tindakan tulis; berhasil menyegarkan daftar lalu memanggil [onSuccess]. */
    fun act(onSuccess: () -> Unit = {}, request: suspend () -> DeviceResult<*>) {
        if (_state.value.acting) return
        _state.update { it.copy(acting = true, actionFailure = null) }
        viewModelScope.launch {
            when (val result = request()) {
                is DeviceResult.Ok -> {
                    _state.update { it.copy(acting = false) }
                    onSuccess()
                    reload()
                }
                is DeviceResult.Failed -> {
                    if (result.failure == AppFailure.Unauthorized) {
                        onUnauthorized()
                    } else {
                        _state.update { it.copy(acting = false, actionFailure = result.failure) }
                    }
                }
            }
        }
    }
}
