package id.kongstudio.cafe.feature.mysession

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.core.format.formatRupiahCompact
import id.kongstudio.cafe.feature.sessions.MethodTotal
import id.kongstudio.cafe.feature.sessions.SessionItem
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.session_chart_cash_use
import id.kongstudio.cafe.resources.session_chart_methods
import id.kongstudio.cafe.resources.session_chart_no_sales
import id.kongstudio.cafe.resources.session_chart_split
import id.kongstudio.cafe.resources.session_counted_revenue
import id.kongstudio.cafe.resources.session_cash_revenue
import id.kongstudio.cafe.resources.session_drawer_spent
import id.kongstudio.cafe.resources.session_method_row
import id.kongstudio.cafe.resources.session_methods_failed
import id.kongstudio.cafe.resources.session_noncash_revenue
import id.kongstudio.cafe.resources.session_other_fund_spent
import id.kongstudio.cafe.resources.session_real_revenue
import id.kongstudio.cafe.resources.session_shopping_fund_used
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.columnchart.ColumnChart
import id.kongstudio.cafe.ui.component.detailcard.DetailCard
import id.kongstudio.cafe.ui.component.donutchart.DonutChart
import id.kongstudio.cafe.ui.component.donutchart.DonutSlice
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.component.sectiontitle.SectionTitle
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

/** Rincian metode bayar satu sesi; [Failed] bila server tidak terbaca, sehingga grafik lain tetap tampil. */
internal sealed interface MethodsState {
    data object Loading : MethodsState

    class Ready(val rows: List<MethodTotal>) : MethodsState

    data object Failed : MethodsState
}

/**
 * Uang satu sesi dalam bentuk yang terbaca sekilas: donat tunai dan non tunai di samping angka per metode, batang per metode bayar
 * (tiap rekening dan QRIS sendiri-sendiri), dan batang aliran uang tunai sampai omzet riil.
 */
@Composable
internal fun SessionMoneyCharts(session: SessionItem, methods: MethodsState, modifier: Modifier = Modifier) {
    val spacing = AppTheme.spacing
    val colors = AppTheme.colors
    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(spacing.md)) {
        if (session.revenue <= 0) {
            Notice(stringResource(Res.string.session_chart_no_sales))
            return@Column
        }

        SectionTitle(text = stringResource(Res.string.session_chart_methods))
        Row(horizontalArrangement = Arrangement.spacedBy(spacing.xl), verticalAlignment = Alignment.CenterVertically) {
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(spacing.sm)) {
                AppText(text = stringResource(Res.string.session_chart_split), role = TextRole.Label, color = colors.contentMuted)
                // Satu metode saja berarti satu irisan 100%, yang tidak membandingkan apa pun; angkanya tetap di kartu sebelah.
                val split = listOf(
                    DonutSlice(stringResource(Res.string.session_cash_revenue), session.cashRevenue, colors.primary),
                    DonutSlice(stringResource(Res.string.session_noncash_revenue), session.nonCashRevenue, colors.accent),
                )
                if (split.count { it.value > 0 } >= 2) DonutChart(slices = split, valueText = ::formatRupiah)
            }
            Column(modifier = Modifier.weight(1f)) {
                when (methods) {
                    MethodsState.Loading -> Unit
                    MethodsState.Failed -> InlineMessage(text = stringResource(Res.string.session_methods_failed))
                    is MethodsState.Ready -> DetailCard(
                        rows = methods.rows.map { it.label to stringResource(Res.string.session_method_row, formatRupiah(it.amount), it.transactions) },
                    )
                }
            }
        }
        (methods as? MethodsState.Ready)?.rows?.takeIf { it.size >= 2 }?.let { rows ->
            ColumnChart(
                values = rows.map { it.amount },
                labels = rows.map { it.label },
                axisText = ::formatRupiahCompact,
                colors = methodColors(rows),
                valueText = ::formatRupiah,
            )
        }

        SectionTitle(text = stringResource(Res.string.session_chart_cash_use))
        ColumnChart(
            values = listOf(session.cashRevenue, session.drawerSpent, session.shoppingFundUsed, session.expectedRevenue.coerceAtLeast(0)),
            labels = listOf(
                stringResource(Res.string.session_cash_revenue),
                stringResource(Res.string.session_drawer_spent),
                stringResource(Res.string.session_shopping_fund_used),
                stringResource(Res.string.session_real_revenue),
            ),
            axisText = ::formatRupiahCompact,
            colors = listOf(colors.primary, colors.rose, colors.accent, colors.violet),
            valueText = ::formatRupiah,
        )
        DetailCard(
            rows = listOf(
                stringResource(Res.string.session_cash_revenue) to formatRupiah(session.cashRevenue),
                stringResource(Res.string.session_drawer_spent) to formatRupiah(session.drawerSpent),
                stringResource(Res.string.session_shopping_fund_used) to formatRupiah(session.shoppingFundUsed),
                stringResource(Res.string.session_other_fund_spent) to formatRupiah(session.otherFundSpent),
                stringResource(Res.string.session_real_revenue) to formatRupiah(session.expectedRevenue),
                stringResource(Res.string.session_counted_revenue) to session.actualRevenue?.let(::formatRupiah),
            ),
        )
    }
}

/** Tunai selalu warna teks; non tunai bergiliran warna latar, ungu, rose, dan metode kelima ke atas netral (maksimal empat seri berwarna). */
@Composable
private fun methodColors(rows: List<MethodTotal>): List<Color> {
    val colors = AppTheme.colors
    val categories = listOf(colors.accent, colors.violet, colors.rose)
    var nonCash = 0
    return rows.map { row -> if (row.cash) colors.primary else categories.getOrElse(nonCash++) { colors.outline } }
}
