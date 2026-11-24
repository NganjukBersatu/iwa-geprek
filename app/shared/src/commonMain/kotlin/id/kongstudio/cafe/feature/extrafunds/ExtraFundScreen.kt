package id.kongstudio.cafe.feature.extrafunds

import id.kongstudio.cafe.feature.periods.BranchPeriodsViewModel
import id.kongstudio.cafe.feature.periods.periodDateRange
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.core.format.whenLabel
import id.kongstudio.cafe.core.time.BusinessDay
import id.kongstudio.cafe.feature.admin.PagedListViewModel
import id.kongstudio.cafe.feature.userchoice.UserChoiceRepository
import id.kongstudio.cafe.feature.userchoice.userFilter
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.common_recorded_by
import id.kongstudio.cafe.resources.common_time
import id.kongstudio.cafe.resources.extrafund_canceled
import id.kongstudio.cafe.resources.extrafund_detail_title
import id.kongstudio.cafe.resources.extrafund_empty
import id.kongstudio.cafe.resources.extrafund_extra
import id.kongstudio.cafe.resources.extrafund_hint
import id.kongstudio.cafe.resources.extrafund_method
import id.kongstudio.cafe.resources.extrafund_order_total
import id.kongstudio.cafe.resources.extrafund_purchase
import id.kongstudio.cafe.resources.extrafund_receipt
import id.kongstudio.cafe.resources.extrafund_received
import id.kongstudio.cafe.resources.extrafund_summary
import id.kongstudio.cafe.resources.filter_recorded_by
import id.kongstudio.cafe.resources.nav_extra_funds
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.detailcard.DetailCard
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.resourcelist.ResourceList
import id.kongstudio.cafe.ui.component.resourcelist.sortLabel
import id.kongstudio.cafe.ui.component.resourcelist.timeSortOptions
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource


@Composable
internal fun ExtraFundScreen(
    viewModel: PagedListViewModel<ExtraFund>,
    repository: ExtraFundRepository,
    userChoices: UserChoiceRepository,
    periods: BranchPeriodsViewModel,
    modifier: Modifier = Modifier,
) {
    val state by viewModel.state.collectAsState()
    val totals by repository.totals.collectAsState()
    var detail by remember { mutableStateOf<ExtraFund?>(null) }
    val today = BusinessDay.today()
    val pickers = listOf(userFilter(viewModel, stringResource(Res.string.filter_recorded_by), userChoices))

    ResourceList(
        title = stringResource(Res.string.nav_extra_funds),
        items = state.items,
        page = state.page,
        pageCount = viewModel.pageCount,
        total = state.total,
        pageSize = viewModel.pageSize,
        onPageChange = viewModel::setPage,
        loading = state.loading,
        failure = state.failure,
        onRetry = viewModel::reload,
        emptyText = stringResource(Res.string.extrafund_empty),
        modifier = modifier,
        sortLabel = sortLabel(),
        sortOptions = timeSortOptions(newest = "-recorded_at", oldest = "recorded_at"),
        selectedSort = state.sort,
        onSortChange = viewModel::setSort,
        pickers = pickers,
        dateRange = periodDateRange(viewModel, periods, today),
        summary = {
            AppText(
                text = stringResource(Res.string.extrafund_hint),
                role = TextRole.Caption,
                color = AppTheme.colors.contentMuted,
            )
            if (!state.loading && state.failure == null) {
                AppText(
                    text = stringResource(Res.string.extrafund_summary, totals.count, formatRupiah(totals.total)),
                    role = TextRole.Caption,
                    color = AppTheme.colors.contentMuted,
                )
            }
        },
    ) { fund ->
        val stamp = DateTimeFormat.stamp(fund.at)
        ListRow(
            title = fund.receipt ?: fund.method,
            detail = formatRupiah(fund.extra),
            caption = fund.purchase.takeIf { it.isNotBlank() },
            footnote = listOfNotNull(
                stamp?.let { whenLabel(it) },
                fund.cashier.takeIf { it.isNotBlank() },
                stringResource(Res.string.extrafund_canceled).takeIf { fund.voided },
            ).joinToString(" · "),
            leading = { IconBadge(AppIcons.CashBanknote) },
            opensDetail = true,
            onClick = { detail = fund },
        )
    }

    detail?.let { fund ->
        val stamp = DateTimeFormat.stamp(fund.at)
        AppBottomSheet(title = stringResource(Res.string.extrafund_detail_title), onDismiss = { detail = null }) {
            Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md)) {
                DetailCard(
                    rows = listOf(
                        stringResource(Res.string.extrafund_receipt) to fund.receipt,
                        stringResource(Res.string.common_time) to stamp?.let { whenLabel(it) },
                        stringResource(Res.string.common_recorded_by) to fund.cashier,
                        stringResource(Res.string.extrafund_method) to fund.method,
                        stringResource(Res.string.extrafund_order_total) to formatRupiah(fund.orderTotal),
                        stringResource(Res.string.extrafund_received) to formatRupiah(fund.received),
                        stringResource(Res.string.extrafund_extra) to formatRupiah(fund.extra),
                        stringResource(Res.string.extrafund_purchase) to fund.purchase,
                    ),
                )
            }
        }
    }
}
