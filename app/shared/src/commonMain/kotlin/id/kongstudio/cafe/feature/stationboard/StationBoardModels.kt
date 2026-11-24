package id.kongstudio.cafe.feature.stationboard

import id.kongstudio.cafe.feature.admin.toMoney
import kotlin.time.ExperimentalTime
import kotlin.time.Instant
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement

private const val ReceiptLength = 8
private const val TakeAway = "take_away"

// --- bentuk dari server --------------------------------------------------------

@Serializable
internal class StationDto(
    val id: String,
    val name: String,
    val kind: String,
    @SerialName("target_seconds") val targetSeconds: Int? = null,
    // Jeda bunyi pengingat; 0 mematikannya, dan server lama tanpa kolom ini dianggap 60 detik.
    @SerialName("reminder_seconds") val reminderSeconds: Int = DefaultReminderSeconds,
    // Stasiun ini ditetapkan untuk tablet ini; APK berbeda versi dengan server menganggapnya tidak dipegang.
    val held: Boolean = false,
)

@Serializable
internal class TaskDto(
    val id: String,
    @SerialName("station_id") val stationId: String,
    val stage: String,
    @SerialName("arrived_at") val arrivedAt: String? = null,
    @SerialName("started_at") val startedAt: String? = null,
    @SerialName("started_by") val startedBy: String? = null,
    @SerialName("finished_at") val finishedAt: String? = null,
    @SerialName("finished_by") val finishedBy: String? = null,
    @SerialName("printed_at") val printedAt: String? = null,
    @SerialName("target_seconds") val targetSeconds: Int? = null,
    val correction: String? = null,
    @SerialName("removed_at") val removedAt: String? = null,
    val acknowledged: Boolean = false,
)

@Serializable
internal class LineDto(
    val id: String? = null,
    @SerialName("menu_item_id") val menuItemId: String? = null,
    val name: String,
    val qty: Int = 0,
    val note: String? = null,
    val options: List<String> = emptyList(),
    val tasks: List<TaskDto> = emptyList(),
)

@Serializable
internal class RequestDto(
    val id: String,
    @SerialName("requested_by_id") val requestedById: String,
    @SerialName("requested_by") val requestedBy: String = "",
    val reason: String? = null,
)

@Serializable
internal class DecisionDto(
    val id: String,
    val approved: Boolean,
    @SerialName("decided_by") val decidedBy: String = "",
    val note: String? = null,
)

@Serializable
internal class BoardOrderDto(
    val id: String,
    @SerialName("receipt_number") val receiptNumber: String? = null,
    @SerialName("customer_name") val customerName: String? = null,
    @SerialName("table_no") val tableNo: String? = null,
    @SerialName("order_type") val orderType: String = "",
    val total: JsonElement? = null,
    @SerialName("created_at") val createdAt: String = "",
    val voided: Boolean = false,
    val lines: List<LineDto> = emptyList(),
    val cancellation: RequestDto? = null,
    val decision: DecisionDto? = null,
    @SerialName("left_behind") val leftBehind: Boolean = false,
    @SerialName("session_cashier") val sessionCashier: String? = null,
)

@Serializable
internal class BoardDto(val orders: List<BoardOrderDto> = emptyList(), val truncated: Boolean = false)

@Serializable
internal class HistoryEntryDto(@SerialName("task_id") val taskId: String, @SerialName("order_id") val orderId: String)

@Serializable
internal class HistoryDto(
    val entries: List<HistoryEntryDto> = emptyList(),
    val orders: List<BoardOrderDto> = emptyList(),
    @SerialName("next_cursor") val nextCursor: String? = null,
)

@Serializable
internal class IngredientDto(val name: String, val unit: String? = null, @SerialName("per_portion") val perPortion: String, val total: String)

@Serializable
internal class RecipeDto(
    val portions: Int = 0,
    val ingredients: List<IngredientDto> = emptyList(),
    @SerialName("without_recipe") val withoutRecipe: List<String> = emptyList(),
)

// --- bentuk untuk layar -----------------------------------------------------------

// Jenis stasiun dari server: pembuat (dapur, bar), pengantar ke meja, atau penyerah dibawa pulang di kasir.
internal enum class StationKind(val code: String) {
    Make("make"),
    Deliver("deliver"),
    Handover("handover");

    companion object {
        fun of(code: String) = entries.firstOrNull { it.code == code } ?: Make
    }
}

// Tahap satu item di satu stasiun, dibaca server dari waktu mulai dan selesainya.
internal enum class Stage(val code: String) {
    Waiting("waiting"),
    Started("started"),
    Finished("finished");

    companion object {
        fun of(code: String) = entries.firstOrNull { it.code == code } ?: Waiting
    }
}

internal enum class Correction { Added, Changed }

internal const val DefaultReminderSeconds = 60

@Serializable
internal class StationWorkerDto(
    @SerialName("user_id") val userId: String,
    val name: String,
    @SerialName("role_name") val roleName: String? = null,
    @SerialName("clock_in_at") val clockInAt: String? = null,
    @SerialName("is_login") val isLogin: Boolean = false,
)

/** Karyawan yang bisa dicatat sebagai pelaku satu menu; akun yang login di tablet menjadi pilihan bawaan. */
internal class StationWorker(val userId: String, val name: String, val roleName: String?, val clockInAt: String?, val isLogin: Boolean)

internal fun StationWorkerDto.toModel() = StationWorker(userId = userId, name = name, roleName = roleName, clockInAt = clockInAt, isLogin = isLogin)

internal class Station(val id: String, val name: String, val kind: StationKind, val targetSeconds: Int?, val held: Boolean, val reminderSeconds: Int = DefaultReminderSeconds)

internal class BoardTask(
    val id: String,
    val stationId: String,
    val stage: Stage,
    // Kosong berarti item belum tiba di stasiun ini.
    val arrivedEpoch: Long?,
    val startedEpoch: Long?,
    val startedBy: String?,
    val finishedEpoch: Long?,
    // Kosong pada menu yang selesai berarti ditutup sistem karena tertinggal terlalu lama.
    val finishedBy: String?,
    val printedEpoch: Long?,
    val targetSeconds: Int?,
    val correction: Correction?,
    val removed: Boolean,
    val cleared: Boolean,
)

// Satu baris pesanan; [id] kosong berarti baris ini sudah dihapus lewat koreksi dan [name] berisi apa yang dihapus.
internal class BoardLine(
    val id: String?,
    val menuItemId: String?,
    val name: String,
    val quantity: Int,
    val note: String?,
    val options: List<String>,
    val tasks: List<BoardTask>,
) {
    fun taskAt(stationId: String): BoardTask? = tasks.firstOrNull { it.stationId == stationId }
}

internal class PendingCancellation(val id: String, val requestedById: String, val requestedBy: String, val reason: String?)

internal class CancelDecision(val id: String, val approved: Boolean, val decidedBy: String, val note: String?)

internal class BoardOrder(
    val id: String,
    val receipt: String,
    val customerName: String?,
    val tableNo: String?,
    val takeAway: Boolean,
    val total: Long,
    val createdEpoch: Long,
    val voided: Boolean,
    val lines: List<BoardLine>,
    // Pengajuan pembatalan yang menunggu keputusan di web; selama ada, pesanan terkunci.
    val cancellation: PendingCancellation?,
    val decision: CancelDecision?,
    // Sesi kasir pesanan ini sudah ditutup, sedangkan menunya belum selesai di stasiun.
    val leftBehind: Boolean,
    val sessionCashier: String?,
)

/** Satu baris Riwayat: menu [taskId] yang sudah selesai di stasiun ini beserta pesanannya. */
internal class HistoryEntry(val taskId: String, val order: BoardOrder) {
    val line: BoardLine? get() = order.lines.firstOrNull { line -> line.tasks.any { it.id == taskId } }
    val task: BoardTask? get() = line?.tasks?.firstOrNull { it.id == taskId }
}

internal class HistoryPage(val entries: List<HistoryEntry>, val nextCursor: String?)

internal class Ingredient(val name: String, val unit: String?, val perPortion: String, val total: String)

internal class GroupRecipe(val portions: Int, val ingredients: List<Ingredient>, val withoutRecipe: List<String>)

internal fun StationDto.toModel() = Station(id = id, name = name, kind = StationKind.of(kind), targetSeconds = targetSeconds, held = held, reminderSeconds = reminderSeconds)

internal fun BoardOrderDto.toModel() = BoardOrder(
    id = id,
    receipt = receiptNumber ?: id.take(ReceiptLength),
    customerName = customerName,
    tableNo = tableNo,
    takeAway = orderType == TakeAway,
    total = total.toMoney(),
    createdEpoch = isoToEpoch(createdAt) ?: 0L,
    voided = voided,
    cancellation = cancellation?.let { PendingCancellation(it.id, it.requestedById, it.requestedBy, it.reason) },
    decision = decision?.let { CancelDecision(it.id, it.approved, it.decidedBy, it.note) },
    leftBehind = leftBehind,
    sessionCashier = sessionCashier?.takeIf { it.isNotBlank() },
    lines = lines.map { line ->
        BoardLine(
            id = line.id,
            menuItemId = line.menuItemId,
            name = line.name,
            quantity = line.qty,
            note = line.note,
            options = line.options,
            tasks = line.tasks.map { task ->
                BoardTask(
                    id = task.id,
                    stationId = task.stationId,
                    stage = Stage.of(task.stage),
                    arrivedEpoch = task.arrivedAt?.let(::isoToEpoch),
                    startedEpoch = task.startedAt?.let(::isoToEpoch),
                    startedBy = task.startedBy,
                    finishedEpoch = task.finishedAt?.let(::isoToEpoch),
                    finishedBy = task.finishedBy,
                    printedEpoch = task.printedAt?.let(::isoToEpoch),
                    targetSeconds = task.targetSeconds,
                    correction = when (task.correction) {
                        "added" -> Correction.Added
                        "changed" -> Correction.Changed
                        else -> null
                    },
                    removed = task.removedAt != null,
                    cleared = task.acknowledged,
                )
            },
        )
    },
)

internal fun HistoryDto.toModel(): HistoryPage {
    val byId = orders.associate { it.id to it.toModel() }
    return HistoryPage(entries.mapNotNull { entry -> byId[entry.orderId]?.let { HistoryEntry(entry.taskId, it) } }, nextCursor)
}

internal fun RecipeDto.toModel() = GroupRecipe(
    portions = portions,
    ingredients = ingredients.map { Ingredient(it.name, it.unit, trimQuantity(it.perPortion), trimQuantity(it.total)) },
    withoutRecipe = withoutRecipe,
)

// Takaran dikirim server dengan tiga angka di belakang koma; nol di ujung dibuang supaya terbaca seperti di resep.
private fun trimQuantity(text: String): String =
    if ('.' in text) text.trimEnd('0').trimEnd('.').replace('.', ',') else text

// Detik epoch dari stempel ISO server; tanpa zona dianggap UTC seperti yang disimpan server.
@OptIn(ExperimentalTime::class)
internal fun isoToEpoch(iso: String): Long? {
    if (iso.isBlank()) return null
    val time = iso.substringAfter('T', "")
    val hasZone = time.any { it == 'Z' || it == '+' || it == '-' }
    return runCatching { Instant.parse(if (hasZone) iso else "${iso}Z").epochSeconds }.getOrNull()
}
