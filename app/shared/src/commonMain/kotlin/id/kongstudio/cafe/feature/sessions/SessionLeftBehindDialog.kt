package id.kongstudio.cafe.feature.sessions

import androidx.compose.runtime.Composable
import id.kongstudio.cafe.feature.stationboard.LeftBehindDialog
import id.kongstudio.cafe.feature.stationboard.LeftBehindRow
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.session_left_behind_body
import id.kongstudio.cafe.resources.session_left_behind_title
import id.kongstudio.cafe.resources.station_kasir_dine_in
import id.kongstudio.cafe.resources.station_kasir_table
import id.kongstudio.cafe.resources.station_take_away
import org.jetbrains.compose.resources.stringResource

/** Pengingat pesanan tertinggal di tablet kasir, saat sesi baru dibuka atau tablet dibuka dengan sesi berjalan. */
@Composable
internal fun SessionLeftBehindDialog(orders: List<LeftBehindOrder>, onNow: () -> Unit, onLater: () -> Unit) {
    val takeAway = stringResource(Res.string.station_take_away)
    val dineIn = stringResource(Res.string.station_kasir_dine_in)
    val rows = orders.map { order ->
        val place = when {
            order.takeAway -> takeAway
            order.tableNo != null -> stringResource(Res.string.station_kasir_table, order.tableNo)
            else -> dineIn
        }
        LeftBehindRow(
            key = order.id,
            title = listOfNotNull(order.receipt?.let { "#$it" }, place, order.customerName).joinToString(" · "),
            detail = order.items,
            cashier = order.cashierName,
        )
    }
    LeftBehindDialog(
        title = stringResource(Res.string.session_left_behind_title, orders.size),
        body = stringResource(Res.string.session_left_behind_body),
        rows = rows,
        onNow = onNow,
        onLater = onLater,
    )
}
