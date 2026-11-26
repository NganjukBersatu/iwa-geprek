package id.kongstudio.cafe.feature.cashier

import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.feature.printer.EscPos
import id.kongstudio.cafe.feature.printer.PairedPrinter
import id.kongstudio.cafe.feature.printer.PaperSize
import id.kongstudio.cafe.feature.printer.PrintOutcome
import id.kongstudio.cafe.feature.printer.PrintPlan
import id.kongstudio.cafe.feature.printer.PrinterSlot
import id.kongstudio.cafe.feature.printer.ReceiptLogo
import id.kongstudio.cafe.feature.printer.ThermalPrinters
import id.kongstudio.cafe.feature.printer.twoColumns
import id.kongstudio.cafe.feature.printer.twoColumnsWrapped
import id.kongstudio.cafe.feature.printer.wrapText
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.print_change
import id.kongstudio.cafe.resources.print_complaint_number
import id.kongstudio.cafe.resources.print_discount
import id.kongstudio.cafe.resources.print_free_table
import id.kongstudio.cafe.resources.print_label_cashier
import id.kongstudio.cafe.resources.print_label_order
import id.kongstudio.cafe.resources.print_label_order_name
import id.kongstudio.cafe.resources.print_label_order_type
import id.kongstudio.cafe.resources.print_label_receipt_number
import id.kongstudio.cafe.resources.print_label_table_number
import id.kongstudio.cafe.resources.print_label_ticket_number
import id.kongstudio.cafe.resources.print_label_time
import id.kongstudio.cafe.resources.print_line_note
import id.kongstudio.cafe.resources.print_no_name
import id.kongstudio.cafe.resources.print_order_note
import id.kongstudio.cafe.resources.print_order_with_table
import id.kongstudio.cafe.resources.print_paid_at
import id.kongstudio.cafe.resources.print_printed_by
import id.kongstudio.cafe.resources.print_reprint
import id.kongstudio.cafe.resources.print_subtotal
import id.kongstudio.cafe.resources.print_take_away
import id.kongstudio.cafe.resources.print_ticket_printed_by
import id.kongstudio.cafe.resources.print_total
import id.kongstudio.cafe.resources.print_total_paid
import id.kongstudio.cafe.resources.print_walk_in_customer
import id.kongstudio.cafe.resources.print_wifi_available
import id.kongstudio.cafe.resources.print_wifi_password
import org.jetbrains.compose.resources.getString


/** Identitas outlet di kepala dan kaki struk, dari pengaturan cabang. */
internal class ShopInfo(
    val name: String,
    val address: String,
    val phone: String,
    val thanks: String,
    val hasWifi: Boolean = false,
    val wifiPassword: String = "",
    val complaintNumber: String = "",
    val socialHandles: List<String> = emptyList(),
    /** Jenis pesanan yang terpilih saat pesanan baru dimulai, dari Pengaturan Kasir cabang. */
    val defaultTakeAway: Boolean = false,
)

internal class PrintableLine(
    val name: String,
    val quantity: Int,
    val unitPrice: Long,
    val details: List<String>,
    val note: String?,
    val category: String,
    /** UUID kategori menu; menentukan printer stasiun yang mencetak tiketnya lewat rencana cetak. */
    val categoryId: String?,
    val variants: List<String> = emptyList(),
    val extras: List<PickedExtra> = emptyList(),
)

/** Satu pesanan yang sudah tersimpan, dalam bentuk yang siap dicetak ke struk dan tiket. */
internal class PrintableOrder(
    val receiptNumber: String?,
    val takeAway: Boolean,
    val customerName: String?,
    val tableNo: String?,
    val paymentLabel: String,
    val lines: List<PrintableLine>,
    /** Nama promo yang memberi potongan; null bila pesanan tanpa potongan. */
    val promoName: String?,
    val discount: Long,
    val total: Long,
    val cashReceived: Long?,
    val change: Long,
    val cashier: String,
    val dateText: String,
    val timeText: String,
    val queued: Boolean,
    /** Saat transaksi (detik sejak epoch), untuk baris Waktu dan Terbayar yang sama formatnya dengan struk web. */
    val epochSeconds: Long = 0,
    /** Catatan untuk seluruh pesanan, dicetak paling bawah. */
    val noteLabel: String? = null,
    /** Saat cetak ulang (detik sejak epoch); terisi berarti kertas diberi penanda CETAK ULANG supaya tidak dikira pesanan baru. */
    val reprintedAt: Long? = null,
)

/** Hasil mencetak satu pesanan: slot yang gagal beserta sebabnya; kosong berarti semuanya tercetak. */
internal class PrintReport(val failures: Map<PrinterSlot, PrintOutcome>, val printedAny: Boolean) {
    val ok: Boolean get() = failures.isEmpty()

    /** Printer yang belum dipasang; mencetak ulang ke sana sia-sia sampai dipasang di menu Printer. */
    val unpaired: Set<PrinterSlot> get() = failures.filterValues { it == PrintOutcome.NotPaired }.keys

    /** Printer terpasang yang gagal mencetak; hanya ini yang ditawarkan cetak ulang. */
    val failed: Set<PrinterSlot> get() = failures.filterValues { it != PrintOutcome.NotPaired }.keys
}

/** Struk pelanggan yang identik baris demi baris dengan `bytesStruk` kasir web (frontend/src/lib/strukCetak.ts), dengan kertas 80 mm memakai jalur asli web dan kertas lain melipat teks yang tidak muat. */
internal suspend fun receiptBytes(shop: ShopInfo, order: PrintableOrder, logo: ByteArray?, paper: PaperSize): ByteArray {
    val layout = PaperLayout(paper)
    val doc = EscPos(paper.columns)
    val stamp = receiptDateTime(order.epochSeconds)
    val received = order.cashReceived ?: order.total

    logo?.let { doc.bytes(it) }
    shop.address.split('\n').filter { it.isNotBlank() }.forEach { layout.center(doc, it) }
    if (shop.phone.isNotBlank()) layout.center(doc, shop.phone)

    doc.line(layout.rule)
    layout.left(doc, labeledLine(getString(Res.string.print_label_receipt_number), order.receiptNumber ?: "-", LabelWidth))
    layout.left(doc, labeledLine(getString(Res.string.print_label_time), stamp, LabelWidth))
    layout.left(doc, labeledLine(getString(Res.string.print_label_cashier), order.cashier, LabelWidth))
    layout.left(doc, labeledLine(getString(Res.string.print_label_order_type), orderTypeLabel(order.takeAway), LabelWidth))
    layout.left(doc, labeledLine(getString(Res.string.print_label_order), order.customerName ?: getString(Res.string.print_walk_in_customer), LabelWidth))
    layout.left(doc, labeledLine(getString(Res.string.print_label_table_number), order.tableNo ?: "-", LabelWidth))
    doc.line(layout.rule)

    order.lines.forEach { line ->
        layout.left(doc, layout.columns(layout.cut("${line.quantity}x ${line.name}", 48), formatRupiah(line.unitPrice * line.quantity)))
        line.variants.forEach { layout.left(doc, "   * $it") }
        line.extras.forEach { extra ->
            val name = "   + ${extra.name}${if (extra.count > 1) " x${extra.count}" else ""}"
            layout.left(doc, if (extra.price > 0) layout.columns(layout.cut(name, 36), "(${formatRupiah(extra.price * extra.count)})") else name)
        }
        line.note?.takeIf { it.isNotEmpty() }?.let { layout.left(doc, "   ${getString(Res.string.print_line_note, it)}") }
    }
    doc.line(layout.rule)

    layout.left(doc, layout.columns(getString(Res.string.print_subtotal), formatRupiah(order.total + order.discount)))
    if (order.discount > 0) {
        layout.left(doc, layout.columns("${getString(Res.string.print_discount)}${order.promoName?.let { " ($it)" } ?: ""}", "-${formatRupiah(order.discount)}"))
    }
    doc.printMode(ModeBold)
    layout.left(doc, layout.columns(getString(Res.string.print_total), formatRupiah(order.total)))
    doc.printMode(ModeNormal)
    doc.line(layout.rule)

    layout.left(doc, layout.columns(order.paymentLabel, formatRupiah(received)))
    layout.left(doc, layout.columns(getString(Res.string.print_total_paid), formatRupiah(order.total)))
    layout.left(doc, layout.columns(getString(Res.string.print_change), formatRupiah((received - order.total).coerceAtLeast(0))))

    if (shop.hasWifi) {
        doc.line(layout.rule)
        layout.center(doc, getString(Res.string.print_wifi_available))
        if (shop.wifiPassword.isNotEmpty()) layout.center(doc, getString(Res.string.print_wifi_password, shop.wifiPassword))
        if (shop.complaintNumber.isNotEmpty()) layout.center(doc, getString(Res.string.print_complaint_number, shop.complaintNumber))
    }
    shop.socialHandles.forEach { layout.center(doc, it) }

    doc.line(layout.rule)
    layout.center(doc, getString(Res.string.print_paid_at, stamp))
    layout.center(doc, getString(Res.string.print_printed_by, order.cashier))
    // Ucapan terima kasih sengaja baris terakhir yang dibaca pelanggan sebelum struk disobek.
    if (shop.thanks.isNotEmpty()) {
        doc.line()
        layout.center(doc, shop.thanks)
    }
    order.noteLabel?.let { note ->
        doc.line().line(layout.rule).printMode(ModeBold)
        layout.center(doc, getString(Res.string.print_order_note, note))
        doc.printMode(ModeNormal)
    }
    reprintMark(doc, layout, order.reprintedAt)
    return doc.cut().build()
}

/**
 * Tiket bar atau dapur, identik dengan `bytesTiket` kasir web: judul stasiun (dengan kategori bila semua item
 * satu kategori), identitas pesanan, nama menu huruf besar setinggi dua baris, lalu catatan pesanan paling bawah.
 */
internal suspend fun ticketBytes(station: String, order: PrintableOrder, lines: List<PrintableLine>, paper: PaperSize): ByteArray {
    val layout = PaperLayout(paper)
    val doc = EscPos(paper.columns)
    val category = lines.firstOrNull()?.category?.takeIf { first -> lines.all { it.category == first } }
    val title = station.uppercase() + (category?.let { " - $it" } ?: "")
    val customerName = order.customerName ?: getString(Res.string.print_no_name)
    val orderName = order.tableNo?.let { getString(Res.string.print_order_with_table, it, customerName) } ?: customerName

    layout.center(doc, title)
    doc.line(layout.rule)
    layout.left(doc, labeledLine(getString(Res.string.print_label_ticket_number), order.receiptNumber ?: "-", LabelWidth))
    layout.left(doc, labeledLine(getString(Res.string.print_label_time), ticketDateTime(order.epochSeconds), LabelWidth))
    // Baris Order memang berisi nama kasir, sama seperti tiket web.
    layout.left(doc, labeledLine(getString(Res.string.print_label_order), order.cashier, LabelWidth))
    layout.left(doc, labeledLine(getString(Res.string.print_label_cashier), order.cashier, LabelWidth))
    layout.left(doc, labeledLine(getString(Res.string.print_label_order_type), orderTypeLabel(order.takeAway), LabelWidth))
    layout.left(doc, labeledLine(getString(Res.string.print_label_order_name), orderName, LabelWidth))
    doc.line(layout.rule)

    lines.forEach { line ->
        doc.printMode(ModeTall)
        layout.left(doc, "${line.quantity} ${line.name.uppercase()}")
        doc.printMode(ModeNormal)
        line.variants.forEach { layout.left(doc, "  * $it") }
        line.extras.filter { it.count > 0 }.forEach { extra ->
            layout.left(doc, "  + ${extra.name}${if (extra.count > 1) " x${extra.count}" else ""}")
        }
        line.note?.takeIf { it.isNotEmpty() }?.let { layout.left(doc, "  - $it") }
    }

    doc.line(layout.rule)
    layout.center(doc, getString(Res.string.print_ticket_printed_by, order.cashier))
    order.noteLabel?.let { note ->
        doc.line().printMode(ModeTall)
        layout.left(doc, getString(Res.string.print_order_note, note))
        doc.printMode(ModeNormal)
    }
    reprintMark(doc, layout, order.reprintedAt)
    return doc.cut().build()
}

/** Penanda cetak ulang beserta jamnya di ujung kertas; tidak dicetak pada cetakan pertama. */
internal suspend fun reprintMark(doc: EscPos, layout: PaperLayout, reprintedAt: Long?) {
    val at = reprintedAt ?: return
    doc.line(layout.rule).printMode(ModeBold)
    layout.center(doc, getString(Res.string.print_reprint, DateTimeFormat.stampAt(at).time.replace(':', '.')))
    doc.printMode(ModeNormal)
}

private const val ModeNormal = 0x00
private const val ModeBold = 0x08
private const val ModeTall = 0x10
private const val WebWideColumns = 48
private const val LabelWidth = 11

/** Satu baris "label : isi" dengan label dirapatkan ke lebar tetap supaya titik duanya sejajar di kertas. */
internal fun labeledLine(label: String, value: String, width: Int): String = "${label.padEnd(width)}: $value"

/** Label jenis pesanan seperti `labelJenisOrder` web. */
private suspend fun orderTypeLabel(takeAway: Boolean) = getString(if (takeAway) Res.string.print_take_away else Res.string.print_free_table)

/** Aturan tata letak satu ukuran kertas, sama dengan struk web: 80 mm tanpa lipat, kertas lain dilipat per kata. */
internal class PaperLayout(paper: PaperSize) {
    private val width = paper.columns
    private val original = paper == PaperSize.Mm80 && width == WebWideColumns
    val rule = "-".repeat(width)

    private fun wrap(text: String): List<String> = if (original) listOf(text) else wrapText(text, width)

    fun center(doc: EscPos, text: String) {
        doc.align(center = true)
        wrap(text).forEach { doc.line(it) }
    }

    fun left(doc: EscPos, text: String) {
        doc.align()
        wrap(text).forEach { doc.line(it) }
    }

    fun columns(left: String, right: String): String =
        if (original) twoColumns(left, right, width) else twoColumnsWrapped(left, right, width)

    /** Jalur 80 mm memotong label panjang seperti web; kertas lain melipatnya. */
    fun cut(text: String, max: Int): String = if (original) text.take(max) else text
}

/** Menu pesanan per stasiun yang tiketnya dicetak dari kasir ini, dalam urutan stasiun pada rencana cetak; stasiun pengantar menerima seluruh pesanan. */
internal fun ticketGroups(plan: PrintPlan, lines: List<PrintableLine>): List<Pair<PlanStationRef, List<PrintableLine>>> =
    plan.stations.filter { !it.held }.mapNotNull { station ->
        val mine = if (station.delivers) lines else lines.filter { plan.sentFromHere(it.categoryId)?.id == station.id }
        mine.takeIf { it.isNotEmpty() }?.let { PlanStationRef(station.id, station.name, station.delivers) to it }
    }

/** Stasiun tujuan satu tiket; cukup nama untuk judul kertas dan UUID untuk slot printernya. */
internal class PlanStationRef(val id: String, val name: String, val delivers: Boolean = false) {
    val slot: PrinterSlot get() = PrinterSlot.station(id)
}

/**
 * Mencetak struk dan tiket pada printer yang terpasang menurut [plan], dengan satu printer gagal tidak menghentikan yang lain
 * dan hasilnya dilaporkan per slot. Rencana yang belum terbaca ([plan] null) tetap mencetak struk supaya penjualan tidak tanpa bukti.
 * Printer yang terputus tidak dialihkan ke printer lain.
 */
internal suspend fun printOrder(
    printers: ThermalPrinters,
    shop: ShopInfo,
    plan: PrintPlan?,
    order: PrintableOrder,
    only: Set<PrinterSlot>? = null,
): PrintReport {
    val paired = printers.paired.value
    val failures = LinkedHashMap<PrinterSlot, PrintOutcome>()
    var printed = false

    suspend fun send(slot: PrinterSlot, bytes: suspend (PairedPrinter) -> ByteArray) {
        if (only != null && slot !in only) return
        // Printer yang dibutuhkan tapi belum dipasang dicatat, supaya layar tidak menyebut struknya tercetak.
        val printer = paired[slot] ?: run {
            failures[slot] = PrintOutcome.NotPaired
            return
        }
        val outcome = printers.print(slot, bytes(printer))
        if (outcome == PrintOutcome.Ok) printed = true else failures[slot] = outcome
    }

    if (plan?.receipt != false) {
        send(PrinterSlot.Receipt) { printer -> receiptBytes(shop, order, ReceiptLogo.forPrinter(printer), printer.paper) }
    }
    plan?.let { ticketGroups(it, order.lines) }.orEmpty().forEach { (station, lines) ->
        // Struk antar baru aktif setelah printer pengantar dipasang; sebelum itu dilewati tanpa peringatan.
        if (station.delivers && station.slot !in paired) return@forEach
        send(station.slot) { printer -> ticketBytes(station.name, order, lines, printer.paper) }
    }

    return PrintReport(failures, printed)
}
