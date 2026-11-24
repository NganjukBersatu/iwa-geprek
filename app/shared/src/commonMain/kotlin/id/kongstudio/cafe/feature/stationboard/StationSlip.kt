package id.kongstudio.cafe.feature.stationboard

import id.kongstudio.cafe.feature.cashier.PaperLayout
import id.kongstudio.cafe.feature.cashier.labeledLine
import id.kongstudio.cafe.feature.cashier.reprintMark
import id.kongstudio.cafe.feature.cashier.ticketDateTime
import id.kongstudio.cafe.feature.printer.EscPos
import id.kongstudio.cafe.feature.printer.PaperSize
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.print_destination_no_table
import id.kongstudio.cafe.resources.print_destination_table
import id.kongstudio.cafe.resources.print_destination_take_away
import id.kongstudio.cafe.resources.print_label_entered
import id.kongstudio.cafe.resources.print_label_name
import id.kongstudio.cafe.resources.print_label_ticket_number
import org.jetbrains.compose.resources.getString

private const val ModeNormal = 0x00
private const val ModeTall = 0x10
private const val ModeLarge = 0x30
private const val LabelWidth = 8

/** Satu struk pesanan: satu menu dari satu pesanan, diletakkan di bawah piring atau gelasnya supaya pengantar tahu tujuannya. */
internal class StationSlip(val orderId: String, val taskId: String, val bytes: ByteArray)

/** Struk pesanan; menu yang sama di pesanan yang sama sudah satu baris, pesanan berbeda selalu struk sendiri, dan [reprintedAt] menandai cetak ulang. */
internal suspend fun stationSlips(station: Station, orders: List<BoardOrder>, taskIds: Set<String>, paper: PaperSize, reprintedAt: Long? = null): List<StationSlip> =
    orders.sortedBy { it.createdEpoch }.flatMap { order ->
        order.lines.mapNotNull { line ->
            val task = line.taskAt(station.id)?.takeIf { it.id in taskIds && !it.removed } ?: return@mapNotNull null
            StationSlip(order.id, task.id, slipBytes(station.name, order, line, paper, reprintedAt))
        }
    }

private suspend fun slipBytes(station: String, order: BoardOrder, line: BoardLine, paper: PaperSize, reprintedAt: Long?): ByteArray {
    val layout = PaperLayout(paper)
    val doc = EscPos(paper.columns)
    val destination = when {
        order.takeAway -> getString(Res.string.print_destination_take_away)
        !order.tableNo.isNullOrBlank() -> getString(Res.string.print_destination_table, order.tableNo.trim().uppercase())
        else -> getString(Res.string.print_destination_no_table)
    }

    layout.center(doc, station.uppercase())
    doc.line(layout.rule)
    doc.printMode(ModeLarge)
    layout.center(doc, destination)
    doc.printMode(ModeNormal)
    layout.left(doc, labeledLine(getString(Res.string.print_label_ticket_number), order.receipt, LabelWidth))
    order.customerName?.takeIf { it.isNotBlank() }?.let { layout.left(doc, labeledLine(getString(Res.string.print_label_name), it.trim(), LabelWidth)) }
    layout.left(doc, labeledLine(getString(Res.string.print_label_entered), ticketDateTime(order.createdEpoch), LabelWidth))
    doc.line(layout.rule)

    doc.printMode(ModeTall)
    layout.left(doc, "${line.quantity}x ${line.name.uppercase()}")
    doc.printMode(ModeNormal)
    line.options.forEach { layout.left(doc, "  * $it") }
    line.note?.takeIf { it.isNotBlank() }?.let { layout.left(doc, "  - ${it.trim()}") }
    // Penanda cetak ulang sudah diawali garis sendiri.
    if (reprintedAt == null) doc.line(layout.rule) else reprintMark(doc, layout, reprintedAt)
    return doc.cut().build()
}
