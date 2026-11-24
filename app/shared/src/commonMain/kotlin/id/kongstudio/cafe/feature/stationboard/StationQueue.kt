package id.kongstudio.cafe.feature.stationboard

// Satu tujuan dalam kelompok: satu baris pesanan dengan tugasnya di stasiun ini.
internal class Portion(val order: BoardOrder, val line: BoardLine, val task: BoardTask)

// Baris antrean: beberapa tugas dengan tahap yang sama yang dikerjakan sekaligus; [key] tetap selama isinya sama.
internal class QueueGroup(
    val key: String,
    val title: String,
    val detail: String?,
    val stage: Stage,
    val portions: List<Portion>,
    // Saat mulai dihitung: waktu tiba untuk yang menunggu, waktu mulai untuk yang sedang dikerjakan.
    val sinceEpoch: Long,
    // Target hitung mundur; hanya untuk yang sedang dikerjakan, kelompok memakai target paling ketat.
    val targetSeconds: Int?,
    val correction: Correction?,
    // Item pesanan yang sama yang belum tiba di sini, untuk pengantar yang menunggu sisa pesanan.
    val notArrived: Int,
    // Sesi kasir pesanannya sudah ditutup; kelompok ini dipisah dan tampil paling atas.
    val leftBehind: Boolean,
    // Kasir sesi asal pesanan tertinggal, untuk keterangan "dari sesi".
    val sessionCashiers: List<String>,
) {
    val units: Int get() = portions.sumOf { it.line.quantity }
    val taskIds: List<String> get() = portions.map { it.task.id }
}

// Baris yang harus dihentikan stasiun: dihapus lewat koreksi atau pesanannya dibatalkan, sampai ditekan Mengerti.
internal class StopAlert(val key: String, val order: BoardOrder, val labels: List<String>, val taskIds: List<String>, val voided: Boolean)

// Pesanan yang terkunci karena pengajuan pembatalan; tampil sendiri supaya tidak ikut dikerjakan bersama kelompok lain.
internal class LockedOrder(val order: BoardOrder, val portions: List<Portion>)

internal class StationQueue(
    val alerts: List<StopAlert>,
    val locked: List<LockedOrder>,
    val started: List<QueueGroup>,
    val waiting: List<QueueGroup>,
) {
    val isEmpty: Boolean get() = alerts.isEmpty() && locked.isEmpty() && started.isEmpty() && waiting.isEmpty()

    fun find(key: String): QueueGroup? = started.firstOrNull { it.key == key } ?: waiting.firstOrNull { it.key == key }
}

// Menyusun antrean satu stasiun dari papan; aturan pengelompokan mengikuti jenis stasiun, bukan namanya.
internal fun queueOf(station: Station, orders: List<BoardOrder>, labels: DestinationLabels): StationQueue {
    val alerts = mutableListOf<StopAlert>()
    val locked = mutableListOf<LockedOrder>()
    val active = mutableListOf<Portion>()
    for (order in orders) {
        val mine = order.lines.mapNotNull { line -> line.taskAt(station.id)?.let { Portion(order, line, it) } }
        val stop = mine.filter { !it.task.cleared && it.task.arrivedEpoch != null && it.task.stage != Stage.Finished && (it.task.removed || order.voided) }
        if (stop.isNotEmpty()) {
            alerts += StopAlert("stop:${order.id}", order, stop.map { lineLabel(it.line) }, stop.map { it.task.id }, order.voided)
        }
        if (order.voided) continue
        val working = mine.filter { !it.task.removed && it.task.arrivedEpoch != null && it.task.stage != Stage.Finished }
        if (working.isEmpty()) continue
        if (order.cancellation != null) locked += LockedOrder(order, working) else active += working
    }
    val notArrived = orders.associate { order ->
        order.id to order.lines.count { line -> line.taskAt(station.id)?.let { !it.removed && it.arrivedEpoch == null } == true }
    }
    val groups = when (station.kind) {
        StationKind.Make -> active.groupBy { "${it.order.leftBehind}:${it.task.stage}:${it.line.menuItemId ?: it.line.name}:${it.line.options}:${it.line.note.orEmpty()}" }
        StationKind.Deliver -> active.groupBy { "${it.order.leftBehind}:${it.task.stage}:${it.order.tableNo?.trim()?.lowercase()?.takeIf { table -> table.isNotEmpty() } ?: it.order.id}" }
        StationKind.Handover -> active.groupBy { "${it.order.leftBehind}:${it.task.stage}:${it.order.id}" }
    }.map { (key, portions) -> groupOf(key, station.kind, portions, notArrived, labels) }

    // Tertinggal paling atas, lalu yang paling lama menunggu.
    val order = compareBy<QueueGroup>({ !it.leftBehind }, { it.sinceEpoch })
    val started = groups.filter { it.stage == Stage.Started }.sortedWith(order)
    val waiting = groups.filter { it.stage == Stage.Waiting }.sortedWith(order)
    return StationQueue(alerts, locked.sortedBy { it.order.createdEpoch }, started, waiting)
}

private fun groupOf(
    key: String,
    kind: StationKind,
    portions: List<Portion>,
    notArrived: Map<String, Int>,
    labels: DestinationLabels,
): QueueGroup {
    val first = portions.first()
    val stage = first.task.stage
    val since = portions.minOf { (if (stage == Stage.Started) it.task.startedEpoch else it.task.arrivedEpoch) ?: it.order.createdEpoch }
    val title = when (kind) {
        StationKind.Make -> first.line.name
        else -> labels.of(first.order)
    }
    val detail = when (kind) {
        StationKind.Make -> (first.line.options + listOfNotNull(first.line.note)).joinToString(" · ").ifBlank { null }
        else -> portions.joinToString(", ") { lineLabel(it.line) }
    }
    return QueueGroup(
        key = key,
        title = title,
        detail = detail,
        stage = stage,
        portions = portions.sortedBy { it.order.createdEpoch },
        sinceEpoch = since,
        targetSeconds = if (stage == Stage.Started) portions.mapNotNull { it.task.targetSeconds }.minOrNull() else null,
        correction = portions.firstNotNullOfOrNull { it.task.correction },
        notArrived = if (kind == StationKind.Make) 0 else portions.map { it.order.id }.distinct().sumOf { notArrived[it] ?: 0 },
        leftBehind = first.order.leftBehind,
        sessionCashiers = portions.mapNotNull { it.order.sessionCashier }.distinct(),
    )
}

internal fun lineLabel(line: BoardLine): String = if (line.quantity > 0) "${line.quantity}x ${line.name}" else line.name

// Kata tujuan pesanan dari teks layar; dibuat sekali di layar lalu dipakai aturan antrean yang bukan composable.
internal class DestinationLabels(private val tablePattern: (String) -> String, private val takeAway: String) {
    // Meja, atau nama dan nomor untuk yang dibawa pulang.
    fun of(order: BoardOrder): String {
        val table = order.tableNo?.trim().orEmpty()
        return when {
            order.takeAway -> listOfNotNull(takeAway, order.customerName?.takeIf { it.isNotBlank() }, "#${order.receipt}").joinToString(" · ")
            table.isNotEmpty() -> tablePattern(table)
            else -> listOfNotNull(order.customerName?.takeIf { it.isNotBlank() }, "#${order.receipt}").joinToString(" · ")
        }
    }

    // Nota untuk ditulis di samping [of]; null bila [of] sudah memuatnya, supaya nota tidak tampil dua kali.
    fun receiptBeside(order: BoardOrder): String? {
        val receipt = "#${order.receipt}"
        return receipt.takeIf { order.receipt.isNotBlank() && it !in of(order) }
    }
}
