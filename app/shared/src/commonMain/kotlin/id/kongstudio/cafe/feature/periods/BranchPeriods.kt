package id.kongstudio.cafe.feature.periods

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.feature.admin.AdminApi
import id.kongstudio.cafe.feature.admin.ListParam
import id.kongstudio.cafe.feature.admin.PagedListViewModel
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.feature.devicesetup.map
import id.kongstudio.cafe.feature.network.LiveChange
import id.kongstudio.cafe.ui.component.resourcelist.ResourceDateRange
import id.kongstudio.cafe.ui.component.resourcelist.ResourcePeriod
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.serialization.Serializable
import kotlinx.serialization.builtins.ListSerializer

internal const val PeriodsPath = "/v2/operational/periods"

// Periode cabang diatur di web; perubahannya sampai ke tablet lewat sinyal /v2/live tabel ini.
internal val PeriodTables = setOf("branch_periods")

/**
 * Penanda rentang daftar masih mengikuti periode berjalan; "0" berarti orang memilih rentangnya sendiri, sehingga pergantian
 * periode atau periode yang baru terbaca tidak menimpa pilihannya. Tidak pernah dikirim ke server.
 */
internal const val RangeFollowsPeriod = "range_follows_period"
private const val Follows = "1"
private const val Chosen = "0"

/** Satu periode tutup buku cabang tablet ini, tanggal ISO; [running] untuk periode yang memuat hari ini. */
internal class BranchPeriod(val start: String, val end: String, val running: Boolean)

@Serializable
private class BranchPeriodDto(val start: String, val end: String, val running: Boolean = false)

internal class BranchPeriodRepository(private val api: AdminApi) {
    suspend fun list(): DeviceResult<List<BranchPeriod>> =
        api.get(PeriodsPath, ListSerializer(BranchPeriodDto.serializer())).map { rows -> rows.map { BranchPeriod(it.start, it.end, it.running) } }
}

/** Periode cabang untuk semua daftar bertanggal di tablet, dimuat sekali per karyawan dan diikuti lewat /v2/live. */
internal class BranchPeriodsViewModel(
    private val repository: BranchPeriodRepository,
    changes: Flow<LiveChange>,
    private val onUnauthorized: () -> Unit,
) : ViewModel() {
    private val _periods = MutableStateFlow<List<BranchPeriod>>(emptyList())
    val periods: StateFlow<List<BranchPeriod>> = _periods.asStateFlow()

    init {
        viewModelScope.launch { load() }
        viewModelScope.launch { changes.collect { load() } }
    }

    // Gagal dibaca berarti periode terakhir tetap dipakai, atau hari ini bila belum pernah terbaca; daftar tetap bisa dibuka.
    private suspend fun load() {
        when (val result = repository.list()) {
            is DeviceResult.Ok -> _periods.value = result.value
            is DeviceResult.Failed -> if (result.failure == AppFailure.Unauthorized) onUnauthorized()
        }
    }

    /** Parameter awal daftar baru: periode berjalan sampai hari ini. */
    fun initialParams(today: String, fromKey: String = ListParam.From, toKey: String = ListParam.To): Map<String, String> {
        val (from, to) = defaultRange(_periods.value, today)
        return mapOf(fromKey to from, toKey to to, RangeFollowsPeriod to Follows)
    }
}

/** Rentang bawaan: awal periode berjalan sampai hari ini; hari ini saja selama periode belum terbaca. */
private fun defaultRange(periods: List<BranchPeriod>, today: String): Pair<String, String> {
    val running = periods.firstOrNull { it.running } ?: return today to today
    return running.start to minOf(running.end, today)
}

/**
 * Rentang tanggal satu daftar: bawaannya periode berjalan cabang yang diatur di web, periode lain bisa dipilih di Filter, dan
 * rentang yang dipilih sendiri tidak ditimpa saat periode berganti.
 */
@Composable
internal fun periodDateRange(
    viewModel: PagedListViewModel<*>,
    periods: BranchPeriodsViewModel,
    today: String,
    fromKey: String = ListParam.From,
    toKey: String = ListParam.To,
): ResourceDateRange {
    val list by periods.periods.collectAsState()
    val state by viewModel.state.collectAsState()
    val (defaultFrom, defaultTo) = defaultRange(list, today)
    LaunchedEffect(defaultFrom, defaultTo) {
        val params = viewModel.state.value.params
        val follows = params[RangeFollowsPeriod] != Chosen
        if (follows && (params[fromKey] != defaultFrom || params[toKey] != defaultTo)) {
            viewModel.setParams(fromKey to defaultFrom, toKey to defaultTo, RangeFollowsPeriod to Follows)
        }
    }
    return ResourceDateRange(
        from = state.params[fromKey] ?: defaultFrom,
        to = state.params[toKey] ?: defaultTo,
        defaultFrom = defaultFrom,
        defaultTo = defaultTo,
        today = today,
        periods = list.map { ResourcePeriod(from = it.start, to = minOf(it.end, today), running = it.running) },
        onChange = { from, to ->
            val chosen = if (from == defaultFrom && to == defaultTo) Follows else Chosen
            viewModel.setParams(fromKey to from, toKey to to, RangeFollowsPeriod to chosen)
        },
    )
}
