package id.kongstudio.cafe.feature.schedule

import id.kongstudio.cafe.core.failure.AppFailure
import androidx.compose.ui.graphics.Color
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.format.YearMonth
import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.ui.theme.color.parseHexColor
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

internal data class ScheduleUiState(
    val month: YearMonth,
    /** Tanggal hari ini "YYYY-MM-DD" menurut jam server (WIB). */
    val today: String,
    /** Tanggal terpilih "YYYY-MM-DD". */
    val selected: String,
    /** Jadwal seluruh staf pada [month]. */
    val items: List<ScheduleItem> = emptyList(),
    val loading: Boolean = true,
    val failure: AppFailure? = null,
    /** Cabang tempat jadwal berlaku; null selama belum diketahui. */
    val outletName: String? = null,
    /** Hanya jadwal milik pengguna; kalender mewarnai tanggalnya sesuai kode. */
    val onlyMine: Boolean = false,
) {
    private val visible: List<ScheduleItem>
        get() = if (onlyMine) items.filter { it.mine } else items

    /** Bulan berikutnya hanya sampai satu bulan setelah bulan berjalan. */
    val canGoNext: Boolean get() = month != DateTimeFormat.monthOf(today).next()

    /** Jadwal pada tanggal terpilih: milik sendiri lebih dulu, lalu menurut jam dan nama. */
    val dayItems: List<ScheduleItem>
        get() = visible.filter { it.date == selected }
            .sortedWith(compareBy({ !it.mine }, { it.code?.start ?: "99:99" }, { it.userName }))

    val markers: Map<String, List<Color?>>
        get() = if (onlyMine) {
            emptyMap()
        } else {
            visible.groupBy { it.date }.mapValues { (_, entries) ->
                entries.map { it.code?.color }.distinct().map { parseHexColor(it) }
            }
        }

    /** Warna blok per tanggal untuk jadwal milik sendiri; kosong bila filter mati. */
    val fills: Map<String, Color>
        get() = if (onlyMine) {
            visible.mapNotNull { item -> parseHexColor(item.code?.color)?.let { item.date to it } }.toMap()
        } else {
            emptyMap()
        }

    /** Tanggal bertugas milik sendiri; berdenyut di kalender hanya selama filter "Jadwal saya" mati. */
    val pulses: Map<String, Color?>
        get() = if (onlyMine) {
            emptyMap()
        } else {
            items.filter { it.mine && !it.off }.associate { it.date to parseHexColor(it.code?.color) }
        }

    /** Kode yang dipakai pada bulan ini, untuk keterangan. */
    val codes: List<ShiftCode>
        get() = items.mapNotNull { it.code }.distinctBy { it.id }.sortedBy { it.code }
}

internal class ScheduleViewModel(
    private val repository: ScheduleRepository,
    private val onSessionExpired: () -> Unit,
) : ViewModel() {
    private val today = DateTimeFormat.todayWib()
    private val _state = MutableStateFlow(
        ScheduleUiState(month = DateTimeFormat.monthOf(today), today = today, selected = today),
    )
    val state: StateFlow<ScheduleUiState> = _state.asStateFlow()
    private var job: Job? = null

    fun previousMonth() = changeMonth(_state.value.month.previous())

    fun nextMonth() {
        if (_state.value.canGoNext) changeMonth(_state.value.month.next())
    }

    fun toggleOnlyMine() = _state.update { it.copy(onlyMine = !it.onlyMine) }

    fun select(date: String) = _state.update { it.copy(selected = date) }

    fun load() {
        job?.cancel()
        _state.update { it.copy(loading = true, failure = null) }
        val month = _state.value.month
        job = viewModelScope.launch {
            when (val result = repository.load(month)) {
                is ApiResult.Success -> _state.update {
                    it.copy(
                        items = result.value.items,
                        outletName = result.value.outletName ?: it.outletName,
                        loading = false,
                        today = DateTimeFormat.todayWib(),
                    )
                }
                ApiResult.Unauthorized -> onSessionExpired()
                is ApiResult.Failure -> _state.update { it.copy(loading = false, failure = result.failure) }
            }
        }
    }

    private fun changeMonth(month: YearMonth) {
        val selected = if (DateTimeFormat.monthOf(today) == month) today else DateTimeFormat.firstDay(month)
        _state.update { it.copy(month = month, selected = selected, items = emptyList()) }
        load()
    }
}
