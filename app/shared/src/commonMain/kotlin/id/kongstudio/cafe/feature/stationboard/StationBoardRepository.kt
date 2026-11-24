package id.kongstudio.cafe.feature.stationboard

import id.kongstudio.cafe.feature.admin.AdminApi
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.feature.devicesetup.map
import io.ktor.http.HttpMethod
import kotlinx.serialization.Serializable
import kotlinx.serialization.SerialName
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import kotlinx.serialization.json.putJsonArray

private const val OperationalPath = "/v2/operational"
private const val HistoryPageSize = 30

// Tabel yang perubahannya membuat papan dimuat ulang lewat /v2/live.
internal val BoardTables = setOf(
    "station_tasks", "orders", "order_items", "stations", "station_branch_settings", "cancellation_requests", "device_stations",
)

// Rincian yang terbuka: siapa yang sedang bekerja (absensi) dan resep menu yang dibuat.
internal val StationDetailTables = setOf("attendance_records", "recipe_ingredients", "menu_items", "variant_choice_recipes", "extra_recipes", "ingredients")

// Sesi kasir dibuka atau ditutup: pilihan pelaku kembali ke akun yang login.
internal val CashSessionTables = setOf("cash_sessions")

/** Bagian riwayat stasiun di server: menu yang pesanannya masih berjalan, atau yang sudah tuntas atau dibatalkan. */
internal enum class HistoryPart(val code: String) {
    Moving("moving"),
    Done("done"),
}

// Langkah yang dikirim ke server; nilainya kata yang dikenali rute papan stasiun.
internal enum class StepKind(val action: String) { Start("start"), Finish("finish"), Back("undo"), Clear("acknowledge") }

internal class Board(val orders: List<BoardOrder>, val truncated: Boolean)

@Serializable
internal class ClaimedPrintDto(@SerialName("task_ids") val taskIds: List<String> = emptyList())

// Panggilan papan stasiun atas nama karyawan yang memegang tablet; cabangnya cabang tablet.
internal class StationBoardRepository(private val api: AdminApi) {
    suspend fun stations(): DeviceResult<List<Station>> =
        api.get("$OperationalPath/stations", ListSerializer(StationDto.serializer())).map { list -> list.map { it.toModel() } }

    // Menu yang sudah selesai di satu stasiun, terbaru dulu; [cursor] kosong berarti halaman pertama.
    suspend fun history(stationId: String, part: HistoryPart, cursor: String?): DeviceResult<HistoryPage> =
        api.get(
            "$OperationalPath/station-history",
            HistoryDto.serializer(),
            buildMap<String, Any?> {
                put("station_id", stationId)
                put("limit", HistoryPageSize)
                put("part", part.code)
                cursor?.let { put("cursor", it) }
            },
        ).map { it.toModel() }

    // Karyawan yang bisa dipilih sebagai pelaku di satu stasiun: akun login, ditambah yang sudah absen masuk dengan peran yang dibolehkan.
    suspend fun workers(stationId: String): DeviceResult<List<StationWorker>> =
        api.get("$OperationalPath/station-workers", ListSerializer(StationWorkerDto.serializer()), mapOf("station_id" to stationId)).map { list -> list.map { it.toModel() } }

    suspend fun board(): DeviceResult<Board> =
        api.get("$OperationalPath/station-board", BoardDto.serializer()).map { dto -> Board(dto.orders.map { it.toModel() }, dto.truncated) }

    // Satu langkah untuk satu item atau sekelompok; [seen] tahap yang terlihat di tablet, yang basi ditolak server.
    suspend fun step(step: StepKind, taskIds: List<String>, seen: Stage, workerId: String? = null): DeviceResult<List<BoardOrder>> =
        api.send(
            method = HttpMethod.Post,
            path = "$OperationalPath/station-tasks:${step.action}",
            body = buildJsonObject {
                if (step != StepKind.Clear) put("seen", seen.code)
                // Pelaku hanya untuk langkah kerja; Mengerti pada menu yang dihentikan tidak dikerjakan siapa pun.
                if (step != StepKind.Clear && workerId != null) put("worker_id", workerId)
                putJsonArray("task_ids") { taskIds.forEach { add(JsonPrimitive(it)) } }
            },
            serializer = ListSerializer(BoardOrderDto.serializer()),
        ).map { list -> list.map { it.toModel() } }

    // Server hanya mengembalikan menu yang belum pernah dicetak, jadi dua tablet di satu stasiun tidak mencetak struk yang sama.
    suspend fun claimPrint(taskIds: List<String>): DeviceResult<Set<String>> =
        api.send(
            method = HttpMethod.Post,
            path = "$OperationalPath/station-tasks:claim-print",
            body = buildJsonObject { putJsonArray("task_ids") { taskIds.forEach { add(JsonPrimitive(it)) } } },
            serializer = ClaimedPrintDto.serializer(),
        ).map { it.taskIds.toSet() }

    suspend fun recipe(lineIds: List<String>): DeviceResult<GroupRecipe> =
        api.get("$OperationalPath/station-recipe", RecipeDto.serializer(), mapOf("line_ids" to lineIds.joinToString(","))).map { it.toModel() }

    // Pesanan terkunci sampai pengajuan diputuskan di web; papan memuat ulang lewat sinyal /v2/live.
    suspend fun requestCancel(orderId: String, reason: String): DeviceResult<Unit> =
        api.sendUnit(
            method = HttpMethod.Post,
            path = "$OperationalPath/cancellations",
            body = buildJsonObject {
                put("order_id", orderId)
                reason.trim().takeIf { it.isNotEmpty() }?.let { put("reason", it) }
            },
        )

    suspend fun withdrawCancel(requestId: String): DeviceResult<Unit> =
        api.sendUnit(method = HttpMethod.Delete, path = "$OperationalPath/cancellations/$requestId")
}
