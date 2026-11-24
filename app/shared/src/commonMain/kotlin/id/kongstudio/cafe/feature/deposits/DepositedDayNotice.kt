package id.kongstudio.cafe.feature.deposits

import androidx.compose.runtime.Composable
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.core.format.longDateLabel
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.deposit_day_body
import id.kongstudio.cafe.resources.deposit_day_item
import id.kongstudio.cafe.resources.deposit_day_title
import id.kongstudio.cafe.resources.deposit_day_title_many
import id.kongstudio.cafe.resources.deposit_day_unknown
import id.kongstudio.cafe.ui.component.statusbanner.BannerTone
import id.kongstudio.cafe.ui.component.statusbanner.StatusBanner
import org.jetbrains.compose.resources.stringResource

/** Peringatan sebelum uang hari yang sudah disetor berubah; tidak tampil bila tidak ada yang disetor. */
@Composable
internal fun DepositedDayNotice(check: DayCheck) {
    when (check) {
        DayCheck.Failed -> StatusBanner(text = stringResource(Res.string.deposit_day_unknown), tone = BannerTone.Warning)
        is DayCheck.Ready -> {
            val days = check.deposited
            if (days.isEmpty()) return
            val title = stringResource(if (days.size == 1) Res.string.deposit_day_title else Res.string.deposit_day_title_many)
            val items = days.map { stringResource(Res.string.deposit_day_item, longDateLabel(it.day), formatRupiah(it.deposited)) }
            StatusBanner(text = (listOf(title) + items + stringResource(Res.string.deposit_day_body)).joinToString("\n"), tone = BannerTone.Warning)
        }
        DayCheck.Idle, DayCheck.Checking -> Unit
    }
}
