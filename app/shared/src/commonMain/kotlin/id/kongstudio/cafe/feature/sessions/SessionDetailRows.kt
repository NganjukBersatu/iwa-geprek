package id.kongstudio.cafe.feature.sessions

import androidx.compose.runtime.Composable
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.core.format.whenLabel
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.common_note
import id.kongstudio.cafe.resources.session_actual_cash
import id.kongstudio.cafe.resources.session_canceled
import id.kongstudio.cafe.resources.session_cash_revenue
import id.kongstudio.cafe.resources.session_code
import id.kongstudio.cafe.resources.session_difference
import id.kongstudio.cafe.resources.session_ended
import id.kongstudio.cafe.resources.session_expected_cash
import id.kongstudio.cafe.resources.session_noncash_revenue
import id.kongstudio.cafe.resources.session_opening_cash
import id.kongstudio.cafe.resources.session_spent
import id.kongstudio.cafe.resources.session_started
import id.kongstudio.cafe.resources.session_total_revenue
import id.kongstudio.cafe.resources.session_transactions
import org.jetbrains.compose.resources.stringResource

/** Baris rincian satu sesi untuk `DetailCard`; angka yang belum ada (sesi berjalan) dilewati kartu. */
@Composable
internal fun sessionDetailRows(session: SessionItem): List<Pair<String, String?>> {
    val started = DateTimeFormat.stamp(session.startedAt)
    val ended = session.endedAt?.let { DateTimeFormat.stamp(it) }
    return listOf(
        stringResource(Res.string.session_code) to session.code,
        stringResource(Res.string.session_started) to started?.let { whenLabel(it) },
        stringResource(Res.string.session_ended) to ended?.let { whenLabel(it) },
        stringResource(Res.string.session_opening_cash) to formatRupiah(session.openingCash),
        stringResource(Res.string.session_transactions) to session.transactions.toString(),
        stringResource(Res.string.session_canceled) to session.canceled.toString(),
        stringResource(Res.string.session_total_revenue) to formatRupiah(session.revenue),
        stringResource(Res.string.session_cash_revenue) to formatRupiah(session.cashRevenue),
        stringResource(Res.string.session_noncash_revenue) to formatRupiah(session.nonCashRevenue),
        stringResource(Res.string.session_spent) to formatRupiah(session.spent),
        stringResource(Res.string.session_expected_cash) to formatRupiah(session.expectedCash),
        stringResource(Res.string.session_actual_cash) to session.actualCash?.let { formatRupiah(it) },
        stringResource(Res.string.session_difference) to session.difference?.let { formatRupiah(it) },
        stringResource(Res.string.common_note) to session.note,
    )
}
