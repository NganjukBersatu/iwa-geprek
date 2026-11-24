package id.kongstudio.cafe.feature.mysession

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.feature.sessions.SessionOrder
import id.kongstudio.cafe.feature.sessions.SessionOrderLine
import id.kongstudio.cafe.feature.sessions.sessionDetailRows
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.order_line
import id.kongstudio.cafe.resources.order_line_options
import id.kongstudio.cafe.resources.order_no_receipt
import id.kongstudio.cafe.resources.order_voided
import id.kongstudio.cafe.resources.session_detail_title
import id.kongstudio.cafe.resources.session_orders
import id.kongstudio.cafe.resources.session_orders_empty
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.detailcard.DetailCard
import id.kongstudio.cafe.ui.component.failurestate.FailureState
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.pagedlistcard.PagedListCard
import id.kongstudio.cafe.ui.component.sectiontitle.SectionTitle
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

/** Rincian satu sesi milik sendiri beserta pesanannya, hanya untuk dibaca. */
@Composable
internal fun SessionDetailSheet(detail: SessionDetailState, onRetry: () -> Unit, onDismiss: () -> Unit) {
    AppBottomSheet(title = stringResource(Res.string.session_detail_title), onDismiss = onDismiss) {
        Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md)) {
            DetailCard(rows = sessionDetailRows(detail.session))
            SectionTitle(text = stringResource(Res.string.session_orders))
            val failure = detail.failure
            if (failure != null) {
                FailureState(failure = failure, onRetry = onRetry)
            } else {
                PagedListCard(
                    items = detail.orders.orEmpty(),
                    page = 0,
                    pageCount = 1,
                    onPageChange = {},
                    emptyText = stringResource(Res.string.session_orders_empty),
                    loading = detail.orders == null,
                ) { order -> OrderRow(order) }
            }
        }
    }
}

@Composable
private fun OrderRow(order: SessionOrder) {
    ListRow(
        title = order.receiptNumber ?: stringResource(Res.string.order_no_receipt),
        detail = formatRupiah(order.total),
        caption = order.lines.map { lineText(it) }.joinToString(", "),
        footnote = listOfNotNull(DateTimeFormat.clock(order.createdAt), order.paymentLabel).joinToString(" · "),
        trailing = if (order.voided) {
            { StatusBadge(text = stringResource(Res.string.order_voided), tone = BadgeTone.Danger) }
        } else {
            null
        },
    )
}

@Composable
private fun lineText(line: SessionOrderLine): String =
    if (line.options.isEmpty()) {
        stringResource(Res.string.order_line, line.quantity, line.name)
    } else {
        stringResource(Res.string.order_line_options, line.quantity, line.name, line.options.joinToString(", "))
    }
