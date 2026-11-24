package id.kongstudio.cafe.feature.ingredientstock

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.foundation.layout.Column
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.format.StockQuantity
import id.kongstudio.cafe.core.format.longDateLabel
import id.kongstudio.cafe.core.format.whenLabel
import id.kongstudio.cafe.feature.access.Permission
import id.kongstudio.cafe.feature.access.UserAccess
import id.kongstudio.cafe.feature.admin.PagedListViewModel
import id.kongstudio.cafe.feature.userchoice.UserChoiceRepository
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.common_all
import id.kongstudio.cafe.resources.nav_ingredient_counts
import id.kongstudio.cafe.resources.stock_close_pending
import id.kongstudio.cafe.resources.stock_close_rejected
import id.kongstudio.cafe.resources.stock_close_request
import id.kongstudio.cafe.resources.stock_close_request_after
import id.kongstudio.cafe.resources.stock_close_request_message
import id.kongstudio.cafe.resources.stock_count_note
import id.kongstudio.cafe.resources.stock_ingredients_empty
import id.kongstudio.cafe.resources.stock_opening_filled
import id.kongstudio.cafe.resources.stock_opening_filter_with
import id.kongstudio.cafe.resources.stock_opening_filter_without
import id.kongstudio.cafe.resources.stock_opening_bulk
import id.kongstudio.cafe.resources.stock_opening_hint
import id.kongstudio.cafe.resources.stock_opening_hint_view
import id.kongstudio.cafe.resources.stock_opening_badge_filled
import id.kongstudio.cafe.resources.stock_opening_badge_missing
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import id.kongstudio.cafe.ui.component.iconbadge.IconBadgeTone
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import id.kongstudio.cafe.resources.stock_close_all_done
import id.kongstudio.cafe.resources.stock_close_period
import id.kongstudio.cafe.core.time.BusinessDay
import id.kongstudio.cafe.resources.stock_opening_value
import id.kongstudio.cafe.resources.stock_search
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.confirmsheet.ConfirmSheet
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.resourcelist.ResourceFilter
import id.kongstudio.cafe.ui.component.resourcelist.ResourceList
import id.kongstudio.cafe.ui.component.resourcelist.nameSortOptions
import id.kongstudio.cafe.ui.component.resourcelist.sortLabel
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.statusbanner.BannerTone
import id.kongstudio.cafe.ui.component.statusbanner.StatusBanner
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

/**
 * Stok Opname di tablet: daftar bahan dengan stok awal periode berjalan; mengetuk bahan membuka detailnya untuk mengisi stok awal.
 * Jumlah real dan tutup periode milik admin di web; tablet hanya mengajukan tutup periode.
 */
@Composable
internal fun IngredientCountScreen(
    list: PagedListViewModel<StockIngredient>,
    period: StockPeriodViewModel,
    /** Perjalanan dan riwayat satu bahan; dibuat pemanggil supaya umurnya ikut halaman detail. */
    journey: @Composable (ingredientId: String) -> IngredientJourneyViewModel,
    history: @Composable (ingredientId: String) -> PagedListViewModel<StockMovement>,
    /** Pengisian stok awal sekaligus; dibuat pemanggil supaya umurnya ikut halaman itu. */
    bulk: @Composable () -> OpeningBulkViewModel,
    repository: IngredientStockRepository,
    userChoices: UserChoiceRepository,
    access: UserAccess,
    modifier: Modifier = Modifier,
) {
    val listState by list.state.collectAsState()
    val periodState by period.state.collectAsState()
    var openedId by rememberSaveable { mutableStateOf<String?>(null) }
    var opened by remember { mutableStateOf<StockIngredient?>(null) }
    var bulkOpen by rememberSaveable { mutableStateOf(false) }
    val canEditOpening = access.allows(Permission.StockCount)
    val title = stringResource(Res.string.nav_ingredient_counts)

    if (bulkOpen && canEditOpening) {
        OpeningBulkPage(viewModel = bulk(), repository = repository, listTitle = title, onBack = { bulkOpen = false }, modifier = modifier)
        return
    }
    // Baris halaman daftar ikut segar lewat live; salinan saat diketuk hanya cadangan bila halaman daftar berganti.
    val detail = openedId?.let { id -> listState.items.firstOrNull { it.id == id } ?: opened?.takeIf { it.id == id } }

    if (detail != null) {
        IngredientOpeningPage(
            ingredient = detail,
            journey = journey(detail.id),
            history = history(detail.id),
            repository = repository,
            userChoices = userChoices,
            access = OpeningAccess(
                canEditOpening = canEditOpening,
                canCorrect = access.allows(Permission.StockCorrect),
            ),
            onBack = {
                openedId = null
                opened = null
            },
            modifier = modifier,
        )
        return
    }

    val filters = listOf(
        ResourceFilter("", stringResource(Res.string.common_all)),
        ResourceFilter(OpeningFilled, stringResource(Res.string.stock_opening_filter_with)),
        ResourceFilter(OpeningMissing, stringResource(Res.string.stock_opening_filter_without)),
    )

    ResourceList(
        title = title,
        items = listState.items,
        page = listState.page,
        pageCount = list.pageCount,
        total = listState.total,
        pageSize = list.pageSize,
        onPageChange = list::setPage,
        loading = listState.loading,
        failure = listState.failure,
        onRetry = list::reload,
        emptyText = stringResource(Res.string.stock_ingredients_empty),
        modifier = modifier,
        searchLabel = stringResource(Res.string.stock_search),
        query = listState.query,
        onQueryChange = list::setQuery,
        filters = filters,
        selectedFilter = listState.filter,
        onFilterChange = list::setFilter,
        sortLabel = sortLabel(),
        sortOptions = nameSortOptions(),
        selectedSort = listState.sort,
        onSortChange = list::setSort,
        // Tombol isi sekaligus hanya untuk yang boleh mengisi stok awal, sama dengan tombol Isi stok awal di detail bahan.
        addLabel = stringResource(Res.string.stock_opening_bulk).takeIf { canEditOpening },
        onAdd = { bulkOpen = true }.takeIf { canEditOpening },
        summary = {
            PeriodSummary(
                state = periodState,
                canRequest = access.allows(Permission.StockClosePeriod),
                canEditOpening = canEditOpening,
                onAsk = period::ask,
            )
        },
    ) { ingredient ->
        IngredientRow(
            ingredient = ingredient,
            caption = ingredient.opening?.let { stringResource(Res.string.stock_opening_value, StockQuantity.withUnit(it, ingredient.unit)) },
            onClick = {
                opened = ingredient
                openedId = ingredient.id
            },
            // Ikon kiri dan lencana sama-sama menyatakan keadaan supaya bahan yang belum diisi terlihat tanpa membaca.
            leading = {
                if (ingredient.opening != null) {
                    IconBadge(AppIcons.ClipboardCheck)
                } else {
                    IconBadge(AppIcons.ClipboardX, tone = IconBadgeTone.Warning)
                }
            },
            status = {
                if (ingredient.opening != null) {
                    StatusBadge(text = stringResource(Res.string.stock_opening_badge_filled), tone = BadgeTone.Positive, icon = AppIcons.Check)
                } else {
                    StatusBadge(text = stringResource(Res.string.stock_opening_badge_missing), tone = BadgeTone.Warning, icon = AppIcons.Alert)
                }
            },
        )
    }

    if (periodState.asking) {
        AskCloseSheet(state = periodState, onSend = period::send, onDismiss = period::dismiss)
    }
}

@Composable
private fun PeriodSummary(state: StockPeriodState, canRequest: Boolean, canEditOpening: Boolean, onAsk: () -> Unit) {
    val colors = AppTheme.colors
    Column(verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm)) {
        state.failure?.let { InlineMessage(text = failureText(it)) }
        val current = state.period ?: return@Column
        // Periode yang akan ditutup baru mulai besok berarti semua periode sampai hari ini sudah ditutup.
        val allClosed = current.closeStart > BusinessDay.today()
        AppText(
            text = if (allClosed) {
                stringResource(Res.string.stock_close_all_done)
            } else {
                stringResource(Res.string.stock_close_period, longDateLabel(current.closeStart), longDateLabel(current.closeEnd))
            },
            role = TextRole.Body,
        )
        AppText(text = stringResource(Res.string.stock_opening_filled, current.filled, current.total), role = TextRole.Label)
        // Petunjuk mengisi hanya untuk yang boleh mengisi; yang lain tidak diberi petunjuk yang tidak bisa dilakukan.
        AppText(
            text = stringResource(if (canEditOpening) Res.string.stock_opening_hint else Res.string.stock_opening_hint_view),
            role = TextRole.Caption,
            color = colors.contentMuted,
        )
        val request = current.request
        when (request?.status) {
            CloseRequestStatus.Pending -> StatusBanner(
                text = stringResource(Res.string.stock_close_pending, request.requestedBy.orEmpty(), stampLabel(request.createdAt)),
                tone = BannerTone.Info,
            )
            CloseRequestStatus.Rejected -> StatusBanner(
                text = stringResource(Res.string.stock_close_rejected, request.decidedBy.orEmpty(), stampLabel(request.decidedAt)),
                tone = BannerTone.Warning,
            )
            CloseRequestStatus.Closed, null -> Unit
        }
        if (canRequest && request?.status != CloseRequestStatus.Pending) {
            SecondaryButton(text = stringResource(Res.string.stock_close_request), onClick = onAsk)
        }
    }
}

@Composable
private fun AskCloseSheet(state: StockPeriodState, onSend: (String) -> Unit, onDismiss: () -> Unit) {
    var note by remember { mutableStateOf("") }
    val current = state.period
    ConfirmSheet(
        title = stringResource(Res.string.stock_close_request),
        message = stringResource(Res.string.stock_close_request_message, current?.let { longDateLabel(it.closeStart) }.orEmpty(), current?.let { longDateLabel(it.closeEnd) }.orEmpty()),
        confirmLabel = stringResource(Res.string.stock_close_request),
        onConfirm = { onSend(note) },
        onDismiss = onDismiss,
        enabled = !state.sending,
        notice = {
            StatusBanner(text = stringResource(Res.string.stock_close_request_after, current?.total ?: 0), tone = BannerTone.Warning)
            AppTextField(value = note, onValueChange = { note = it }, label = stringResource(Res.string.stock_count_note))
            state.sendFailure?.let { InlineMessage(text = failureText(it)) }
        },
    )
}

@Composable
internal fun stampLabel(iso: String?): String = DateTimeFormat.stamp(iso)?.let { whenLabel(it) }.orEmpty()
