package id.kongstudio.cafe.feature.mysession

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.core.format.whenLabel
import id.kongstudio.cafe.feature.admin.PagedListViewModel
import id.kongstudio.cafe.feature.sessions.SessionItem
import id.kongstudio.cafe.feature.sessions.SessionParamFrom
import id.kongstudio.cafe.feature.sessions.SessionParamTo
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.common_from
import id.kongstudio.cafe.resources.common_to
import id.kongstudio.cafe.resources.date_any
import id.kongstudio.cafe.resources.date_clear
import id.kongstudio.cafe.resources.session_history
import id.kongstudio.cafe.resources.session_history_empty
import id.kongstudio.cafe.resources.session_row_transactions
import id.kongstudio.cafe.resources.session_running
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.daterangefields.DateRangeFields
import id.kongstudio.cafe.ui.component.failurestate.FailureState
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.pagedlistcard.PagedListCard
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.sectiontitle.SectionTitle
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

/** Daftar berhalaman sesi milik sendiri, terbaru dulu; tanpa tanggal berarti semua sesi. */
@Composable
internal fun SessionHistorySection(history: PagedListViewModel<SessionItem>, onOpen: (SessionItem) -> Unit) {
    val state by history.state.collectAsState()
    val today = remember { DateTimeFormat.todayWib() }
    val from = state.params[SessionParamFrom].orEmpty()
    val to = state.params[SessionParamTo].orEmpty()

    Column(verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md)) {
        SectionTitle(text = stringResource(Res.string.session_history))
        DateRangeFields(
            from = from,
            to = to,
            today = today,
            fromLabel = stringResource(Res.string.common_from),
            toLabel = stringResource(Res.string.common_to),
            onChange = { start, end -> history.setParams(SessionParamFrom to start, SessionParamTo to end) },
            sideBySide = true,
            placeholder = stringResource(Res.string.date_any),
        )
        if (from.isNotEmpty() || to.isNotEmpty()) {
            SecondaryButton(
                text = stringResource(Res.string.date_clear),
                onClick = { history.setParams(SessionParamFrom to "", SessionParamTo to "") },
            )
        }
        val failure = state.failure
        if (failure != null) {
            FailureState(failure = failure, onRetry = history::reload)
        } else {
            PagedListCard(
                items = state.items,
                page = state.page,
                pageCount = history.pageCount,
                onPageChange = history::setPage,
                emptyText = stringResource(Res.string.session_history_empty),
                loading = state.loading,
            ) { item ->
                ListRow(
                    title = DateTimeFormat.stamp(item.startedAt)?.let { whenLabel(it) } ?: item.startedAt,
                    detail = formatRupiah(item.revenue),
                    caption = listOfNotNull(item.code, stringResource(Res.string.session_row_transactions, item.transactions)).joinToString(" · "),
                    leading = { IconBadge(AppIcons.Clock) },
                    trailing = if (item.open) {
                        { StatusBadge(text = stringResource(Res.string.session_running), tone = BadgeTone.Positive) }
                    } else {
                        null
                    },
                    opensDetail = true,
                    onClick = { onOpen(item) },
                )
            }
        }
    }
}
