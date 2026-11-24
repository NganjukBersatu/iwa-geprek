package id.kongstudio.cafe.ui.component.resourcelist

import androidx.compose.foundation.layout.Arrangement
import id.kongstudio.cafe.ui.component.pagetitle.PageTitle
import id.kongstudio.cafe.ui.component.pageframe.PageFrame
import androidx.compose.foundation.layout.Column
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.sort_label
import id.kongstudio.cafe.resources.sort_name_asc
import id.kongstudio.cafe.resources.sort_name_desc
import id.kongstudio.cafe.resources.sort_newest
import id.kongstudio.cafe.resources.sort_oldest
import id.kongstudio.cafe.ui.component.apptext.TextRole
import androidx.compose.foundation.layout.Row
import org.jetbrains.compose.resources.stringResource
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.ui.component.failurestate.FailureState
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.loadable.Loadable
import id.kongstudio.cafe.ui.component.pagedlistcard.PageRange
import id.kongstudio.cafe.ui.component.pagedlistcard.PagedListCard
import id.kongstudio.cafe.core.format.longDateLabel
import id.kongstudio.cafe.resources.common_from
import id.kongstudio.cafe.resources.common_to
import id.kongstudio.cafe.resources.filter_picked_tag
import id.kongstudio.cafe.resources.filter_range_tag
import id.kongstudio.cafe.ui.component.pickerfield.PickerField
import id.kongstudio.cafe.resources.filter_sort_tag
import id.kongstudio.cafe.resources.filter_title
import id.kongstudio.cafe.ui.component.daterangefields.DateRangeFields
import id.kongstudio.cafe.ui.component.dropdownfield.DropdownField
import id.kongstudio.cafe.ui.component.dropdownfield.DropdownOption
import id.kongstudio.cafe.ui.component.filterbar.FilterBar
import id.kongstudio.cafe.ui.component.filterbar.FilterTag
import id.kongstudio.cafe.ui.component.segmentedcontrol.SegmentedControl
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.resources.period_custom
import id.kongstudio.cafe.resources.period_label
import id.kongstudio.cafe.resources.period_option
import id.kongstudio.cafe.resources.period_option_running
import id.kongstudio.cafe.resources.period_running_caption

/** Label satu periode di Filter, dengan penanda periode yang sedang berjalan. */
@Composable
private fun periodLabel(period: ResourcePeriod): String {
    val range = stringResource(Res.string.period_option, longDateLabel(period.from), longDateLabel(period.to))
    return if (period.running) stringResource(Res.string.period_option_running, range) else range
}

/** Satu pilihan penyaring di atas daftar: [value] dikirim ke pemanggil, [label] ditampilkan. */
class ResourceFilter(val value: String, val label: String)

/** Kode urutan baku yang dibaca server di semua daftar: waktu dan huruf; tanda minus di depan berarti turun. */
object SortKey {
    const val Newest = "-time"
    const val Oldest = "time"
    const val NameAsc = "name"
    const val NameDesc = "-name"
}

/** Kode bawaan boleh diganti bila rute daftarnya sudah punya nama kolom sendiri, misalnya pengeluaran yang memakai created_at. */
@Composable
fun timeSortOptions(newest: String = SortKey.Newest, oldest: String = SortKey.Oldest): List<ResourceFilter> = listOf(
    ResourceFilter(newest, stringResource(Res.string.sort_newest)),
    ResourceFilter(oldest, stringResource(Res.string.sort_oldest)),
)

@Composable
fun nameSortOptions(ascending: String = SortKey.NameAsc, descending: String = SortKey.NameDesc): List<ResourceFilter> = listOf(
    ResourceFilter(ascending, stringResource(Res.string.sort_name_asc)),
    ResourceFilter(descending, stringResource(Res.string.sort_name_desc)),
)

/** Urutan bawaan server yang bukan waktu atau huruf, misalnya menu per kategori; kodenya kosong supaya server memakai urutan bawaannya. */
@Composable
fun defaultSortOption(label: String): ResourceFilter = ResourceFilter("", label)

@Composable
fun sortLabel(): String = stringResource(Res.string.sort_label)


/**
 * Penyaring yang pilihannya terlalu banyak untuk dropdown, misalnya "Dicatat oleh": kolomnya membuka lembar pilih sendiri ([onOpen]);
 * [selectedLabel] kosong berarti belum disaring dan kolom menampilkan [allLabel].
 */
class ResourcePicker(
    val label: String,
    val selectedLabel: String?,
    val allLabel: String,
    val onOpen: () -> Unit,
    val onClear: () -> Unit,
)

/** Satu periode tutup buku cabang yang bisa dipilih sebagai rentang; [to] sudah dibatasi sampai hari ini. */
class ResourcePeriod(val from: String, val to: String, val running: Boolean)

/**
 * Rentang tanggal sebuah daftar: [from] dan [to] yang tampil, [defaultFrom] dan [defaultTo] yang berlaku saat filter dihapus,
 * dan [periods] periode cabang yang bisa dipilih langsung di Filter.
 */
class ResourceDateRange(
    val from: String,
    val to: String,
    val defaultFrom: String,
    val defaultTo: String,
    val today: String,
    val onChange: (from: String, to: String) -> Unit,
    val periods: List<ResourcePeriod> = emptyList(),
)

// Kunci pilihan periode di dropdown; rentang yang tidak sama dengan periode mana pun tampil sebagai "Rentang lain".
private const val CustomRangeKey = ""
private fun periodKey(from: String, to: String) = "$from/$to"

/**
 * Kerangka layar daftar kelola: judul dengan tombol tambah, satu komponen filter (cari, periode, filter, dan urutan), pengalih isi ([tabs]),
 * ringkasan, dan daftar berhalaman dengan keterangan jumlah, dengan keadaan memuat, gagal, dan kosong ditangani di sini.
 */
@Composable
fun <T> ResourceList(
    title: String,
    items: List<T>,
    page: Int,
    pageCount: Int,
    /** Jumlah seluruh baris dan ukuran halaman, untuk keterangan "Menampilkan a–b dari n" di bawah daftar. */
    total: Int,
    pageSize: Int,
    onPageChange: (Int) -> Unit,
    loading: Boolean,
    failure: AppFailure?,
    onRetry: () -> Unit,
    emptyText: String,
    modifier: Modifier = Modifier,
    searchLabel: String? = null,
    query: String = "",
    onQueryChange: (String) -> Unit = {},
    /** Pilihan isi yang saling meniadakan, misalnya Varian dan Ekstra; tampil sebagai pengalih di bawah judul, bukan di dalam filter. */
    tabs: List<ResourceFilter> = emptyList(),
    selectedTab: String = "",
    onTabChange: (String) -> Unit = {},
    /** Penyaring isi daftar; pilihan pertama adalah bawaan ("Semua") dan tidak tampil sebagai filter aktif. */
    filters: List<ResourceFilter> = emptyList(),
    filterLabel: String? = null,
    selectedFilter: String = "",
    onFilterChange: (String) -> Unit = {},
    pickers: List<ResourcePicker> = emptyList(),
    dateRange: ResourceDateRange? = null,
    sortLabel: String? = null,
    sortOptions: List<ResourceFilter> = emptyList(),
    selectedSort: String = "",
    onSortChange: (String) -> Unit = {},
    addLabel: String? = null,
    onAdd: (() -> Unit)? = null,
    actionError: String? = null,
    summary: (@Composable ColumnScope.() -> Unit)? = null,
    row: @Composable (T) -> Unit,
) {
    val spacing = AppTheme.spacing

    val defaultFilter = filters.firstOrNull()?.value
    val activeFilter = filters.firstOrNull { it.value == selectedFilter }?.takeIf { selectedFilter != defaultFilter }
    val rangeActive = dateRange != null && (dateRange.from != dateRange.defaultFrom || dateRange.to != dateRange.defaultTo)
    val defaultSort = sortOptions.firstOrNull()?.value
    val activeSort = sortOptions.firstOrNull { it.value == selectedSort }?.takeIf { selectedSort != defaultSort }

    val tags = buildList {
        activeFilter?.let { chosen -> add(FilterTag(chosen.label) { defaultFilter?.let(onFilterChange) }) }
        pickers.forEach { picker ->
            picker.selectedLabel?.let { add(FilterTag(stringResource(Res.string.filter_picked_tag, picker.label, it), picker.onClear)) }
        }
        if (dateRange != null && rangeActive) {
            val label = stringResource(Res.string.filter_range_tag, longDateLabel(dateRange.from), longDateLabel(dateRange.to))
            add(FilterTag(label) { dateRange.onChange(dateRange.defaultFrom, dateRange.defaultTo) })
        }
        activeSort?.let { chosen ->
            add(FilterTag(stringResource(Res.string.filter_sort_tag, chosen.label)) { defaultSort?.let(onSortChange) })
        }
    }
    val clearAll = {
        if (activeFilter != null) defaultFilter?.let(onFilterChange)
        pickers.filter { it.selectedLabel != null }.forEach { it.onClear() }
        if (dateRange != null && rangeActive) dateRange.onChange(dateRange.defaultFrom, dateRange.defaultTo)
        if (activeSort != null) defaultSort?.let(onSortChange)
    }
    val hasFilterContent = filters.isNotEmpty() || pickers.isNotEmpty() || dateRange != null || sortOptions.isNotEmpty()

    // Daftar tanpa kolom cari dan tanpa tombol tambah meletakkan Filter sebaris dengan judul, supaya tidak mengambang sendirian.
    val filterBesideTitle = searchLabel == null && hasFilterContent && (onAdd == null || addLabel == null)

    PageFrame(modifier = modifier) {
        if (!filterBesideTitle) {
            item {
                PageTitle(title = title) {
                    // Aksi utama halaman berlabel, bukan ikon saja, supaya jelas bagaimana menambah data.
                    if (onAdd != null && addLabel != null) {
                        PrimaryButton(text = addLabel, onClick = onAdd, icon = AppIcons.Plus, fullWidth = false)
                    }
                }
            }
        }
        if (searchLabel != null || hasFilterContent) {
            item {
                FilterBar(
                    searchLabel = searchLabel,
                    query = query,
                    onQueryChange = onQueryChange,
                    showButton = hasFilterContent,
                    tags = tags,
                    onClearAll = clearAll,
                    leadingTitle = title.takeIf { filterBesideTitle },
                    leadingRole = TextRole.Headline,
                ) {
                    if (filters.isNotEmpty()) {
                        DropdownField(
                            label = filterLabel ?: stringResource(Res.string.filter_title),
                            options = filters.map { DropdownOption(it.value, it.label) },
                            selectedKey = selectedFilter,
                            onSelect = { onFilterChange(it.orEmpty()) },
                        )
                    }
                    pickers.forEach { picker ->
                        PickerField(label = picker.label, valueText = picker.selectedLabel ?: picker.allLabel, icon = AppIcons.User, onClick = picker.onOpen)
                    }
                    dateRange?.takeIf { it.periods.isNotEmpty() }?.let { range ->
                        val options = range.periods.map { DropdownOption(periodKey(it.from, it.to), periodLabel(it)) } +
                            DropdownOption(CustomRangeKey, stringResource(Res.string.period_custom))
                        val selected = range.periods.firstOrNull { it.from == range.from && it.to == range.to }
                        DropdownField(
                            label = stringResource(Res.string.period_label),
                            options = options,
                            selectedKey = selected?.let { periodKey(it.from, it.to) } ?: CustomRangeKey,
                            onSelect = { key -> range.periods.firstOrNull { periodKey(it.from, it.to) == key }?.let { range.onChange(it.from, it.to) } },
                        )
                    }
                    dateRange?.let { range ->
                        DateRangeFields(
                            from = range.from,
                            to = range.to,
                            today = range.today,
                            fromLabel = stringResource(Res.string.common_from),
                            toLabel = stringResource(Res.string.common_to),
                            onChange = range.onChange,
                            sideBySide = true,
                        )
                    }
                    if (sortOptions.isNotEmpty()) {
                        DropdownField(
                            label = sortLabel ?: stringResource(Res.string.sort_label),
                            options = sortOptions.map { DropdownOption(it.value, it.label) },
                            selectedKey = selectedSort,
                            onSelect = { onSortChange(it.orEmpty()) },
                        )
                    }
                }
            }
        }
        // Keputusan pemilik: tab berada di bawah cari dan Filter, tepat di atas isi.
        if (tabs.isNotEmpty()) {
            item {
                SegmentedControl(
                    options = tabs.map { it.label },
                    selectedIndex = tabs.indexOfFirst { it.value == selectedTab }.coerceAtLeast(0),
                    onSelect = { index -> onTabChange(tabs[index].value) },
                )
            }
        }
        actionError?.let { item { InlineMessage(text = it) } }
        // Periode bawaan tidak tampil sebagai chip, jadi rentangnya disebut di atas daftar supaya isi daftar tidak disangka lengkap.
        if (dateRange != null && dateRange.periods.isNotEmpty() && !rangeActive) {
            item {
                AppText(
                    text = stringResource(Res.string.period_running_caption, longDateLabel(dateRange.from), longDateLabel(dateRange.to)),
                    role = TextRole.Caption,
                    color = AppTheme.colors.contentMuted,
                )
            }
        }
        summary?.let { content ->
            item { Column(verticalArrangement = Arrangement.spacedBy(spacing.sm), content = content) }
        }

        item {
            Loadable(loading = loading) {
                if (failure != null) {
                    FailureState(failure = failure, onRetry = onRetry)
                } else {
                    PagedListCard(
                        items = items,
                        page = page,
                        pageCount = pageCount,
                        onPageChange = onPageChange,
                        emptyText = emptyText,
                        range = PageRange(page = page, pageSize = pageSize, total = total),
                    ) { value -> row(value) }
                }
            }
        }
    }
}
