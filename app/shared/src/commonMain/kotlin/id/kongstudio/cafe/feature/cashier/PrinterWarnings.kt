package id.kongstudio.cafe.feature.cashier

import androidx.compose.runtime.Composable
import id.kongstudio.cafe.feature.printer.PairedPrinter
import id.kongstudio.cafe.feature.printer.PrintPlan
import id.kongstudio.cafe.feature.printer.PrinterLink
import id.kongstudio.cafe.feature.printer.PrinterSlot
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.cashier_list_last
import id.kongstudio.cafe.resources.cashier_printer_station_offline
import id.kongstudio.cafe.resources.cashier_printer_station_unpaired
import id.kongstudio.cafe.ui.component.statusbanner.BannerTone
import id.kongstudio.cafe.ui.component.statusbanner.StatusBanner
import org.jetbrains.compose.resources.stringResource

/** Printer belum dipasang di tablet ini, atau sudah dipasang tetapi sambungannya putus. */
internal enum class PrinterProblem { NotPaired, Offline }

/** Menu di keranjang yang tiketnya ke printer stasiun [stationName] dan belum pasti tercetak. */
internal class PrinterWarning(val stationName: String, val problem: PrinterProblem, val menuNames: List<String>)

/** Peringatan per printer stasiun tanpa tablet untuk menu di keranjang; printer yang sedang menyambung belum dianggap putus. */
internal fun printerWarnings(
    lines: List<CartLine>,
    plan: PrintPlan?,
    paired: Map<PrinterSlot, PairedPrinter>,
    links: Map<PrinterSlot, PrinterLink>,
): List<PrinterWarning> = plan?.stations.orEmpty().filter { !it.held }.mapNotNull { station ->
    val names = lines.filter { line -> plan?.sentFromHere(line.item.categoryId)?.id == station.id }.map { it.item.name }.distinct()
    val problem = when {
        names.isEmpty() -> null
        station.slot !in paired -> PrinterProblem.NotPaired
        links[station.slot] == PrinterLink.Offline -> PrinterProblem.Offline
        else -> null
    }
    problem?.let { PrinterWarning(station.name, it, names) }
}

@Composable
internal fun PrinterWarningBanner(warning: PrinterWarning) {
    val menus = menuList(warning.menuNames)
    val text = when (warning.problem) {
        PrinterProblem.NotPaired -> stringResource(Res.string.cashier_printer_station_unpaired, warning.stationName, menus)
        PrinterProblem.Offline -> stringResource(Res.string.cashier_printer_station_offline, warning.stationName, menus)
    }
    StatusBanner(text = text, tone = BannerTone.Warning)
}

@Composable
private fun menuList(names: List<String>): String =
    if (names.size < 2) {
        names.joinToString()
    } else {
        stringResource(Res.string.cashier_list_last, names.dropLast(1).joinToString(", "), names.last())
    }
