package id.kongstudio.cafe.feature.ingredientstock

import id.kongstudio.cafe.feature.admin.AdminApi
import id.kongstudio.cafe.feature.admin.ChoicePage
import id.kongstudio.cafe.feature.admin.ListPage
import id.kongstudio.cafe.feature.admin.ListParam
import id.kongstudio.cafe.feature.admin.PageRequest
import id.kongstudio.cafe.feature.admin.putText
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import io.ktor.http.HttpMethod
import id.kongstudio.cafe.core.time.BusinessDay
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import kotlinx.serialization.json.putJsonArray

internal const val StockPageSize = 30
private const val StockPath = "/v2/operational/stock"

// Tabel yang perubahannya memuat ulang daftar stok lewat /v2/live: bahan, kartu bahan, opname, dan pengajuan tutup periode.
internal val StockTables = setOf("ingredients", "ingredient_cards", "ingredient_counts", "ingredient_count_requests")

// Daftar "Dipakai di menu" ikut berubah saat resep atau nama menu berubah.
internal val RecipeUseTables = setOf("ingredients", "recipe_ingredients", "menu_items")

internal const val OpeningFilled = "with"
internal const val OpeningMissing = "without"

/** Jenis catatan stok yang punya riwayat sendiri; kodenya dipakai server. */
internal enum class MovementKind(val code: String) { Receipt("receipt"), Waste("waste"), Trial("trial") }

/** [opening] adalah stok awal periode berjalan; null berarti belum diisi. [packageSize] isi satu kemasan beli dalam [unit]. */
internal class StockIngredient(
    val id: String,
    val name: String,
    val unit: String?,
    val category: String?,
    val stock: String,
    val minimum: String,
    val opening: String?,
    val packageSize: String = "1",
) {
    /** Bahan yang dibeli dalam kemasan berisi lebih dari satu satuan bisa dicatat per kemasan. */
    val packaged: Boolean get() = (packageSize.toDoubleOrNull() ?: 0.0) > 1.0

    /** Hanya bahan yang punya batas minimum yang bisa disebut menipis. */
    val low: Boolean
        get() {
            val floor = minimum.toDoubleOrNull() ?: 0.0
            return floor > 0.0 && (stock.toDoubleOrNull() ?: 0.0) <= floor
        }
}

/** Jenis kartu bahan sesuai kode server; [Other] untuk kode yang belum dikenal app versi ini. */
internal enum class CardKind(val code: String) {
    In("masuk"),
    Out("keluar"),
    Waste("rusak"),
    Trial("rnd"),
    Adjustment("penyesuaian"),
    Other(""),
    ;

    companion object {
        fun of(code: String): CardKind = entries.firstOrNull { it.code == code && it != Other } ?: Other
    }
}

/** Di tablet, catatan penjualan, penutupan periode, dan stok awal tidak diubah dari riwayat; masing-masing punya jalurnya sendiri. */
internal class StockMovement(
    val id: String,
    val ingredientName: String,
    val unit: String?,
    val qty: String,
    val kind: CardKind,
    val causeLabel: String?,
    val note: String?,
    val userName: String?,
    val createdAt: String,
    val fromSale: Boolean,
    val fromCount: Boolean,
    val fromOpening: Boolean,
    val proofUrl: String? = null,
) {
    val editable: Boolean get() = !fromSale && !fromCount && !fromOpening
}

internal class WasteCause(val code: String, val label: String)

/** Hasil mencatat: [id] catatan baru, dan [proofSaved] false bila foto yang dilampirkan gagal terunggah walau catatannya tersimpan. */
internal class EntrySaved(val id: String, val proofSaved: Boolean)

internal enum class CloseRequestStatus { Pending, Rejected, Closed }

internal class CloseRequest(
    val status: CloseRequestStatus,
    val note: String?,
    val requestedBy: String?,
    val createdAt: String,
    val decidedBy: String?,
    val decidedAt: String?,
)

/**
 * Periode berjalan: [start] awal stok awalnya (ISO); [closeStart] sampai [closeEnd] rentang yang ditutup berikutnya, sama dengan web;
 * [filled] dari [total] bahan aktif sudah punya stok awal.
 */
internal class OpeningPeriod(
    val start: String,
    val closeStart: String,
    val closeEnd: String,
    val filled: Int,
    val total: Int,
    val request: CloseRequest?,
)

/** Perjalanan stok satu bahan di periode berjalan, dari stok awal sampai stok sekarang. */
internal class StockJourney(
    val start: String,
    val opening: String,
    val openingSet: Boolean,
    val openingBy: String?,
    val openingAt: String?,
    val received: String,
    val sold: String,
    val wasted: String,
    val trial: String,
    val adjusted: String,
    val stock: String,
)

/** Menu yang resepnya memakai bahan ini dan takarannya per porsi. */
internal class RecipeUse(val menuId: String, val menuName: String, val qty: String)

/** Satu baris pengisian stok awal sekaligus; [qty] sudah dirapikan. */
internal class OpeningRow(val ingredientId: String, val qty: String)

/** Hasil satu baris; [error] berisi alasan dari server bila baris itu gagal. */
internal class OpeningRowResult(val ingredientId: String, val error: String?)

// Batas baris satu kiriman massal di server (app/core/bulk.py MAX_ROWS).
internal const val OpeningBulkMax = 500


@Serializable
private class BulkRowDto(val row: Int, val ok: Boolean, val error: String? = null)

@Serializable
private class BulkResultDto(val results: List<BulkRowDto> = emptyList())

internal class IngredientStockRepository(private val api: AdminApi) {
    /** [PageRequest.filter] berisi [OpeningFilled], [OpeningMissing], atau kosong untuk semua bahan. */
    suspend fun ingredients(request: PageRequest): DeviceResult<ListPage<StockIngredient>> =
        when (
            val result = api.get(
                path = "$StockPath/ingredients",
                serializer = IngredientPageDto.serializer(),
                query = mapOf(
                    "page" to request.page + 1,
                    "size" to StockPageSize,
                    "search" to request.query,
                    "sort" to request.sort,
                    "opening" to request.filter.ifBlank { null },
                ),
            )
        ) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(ListPage(result.value.items.map { it.toModel() }, result.value.total))
        }

    /** Pilihan bahan untuk dicatat, dicari di server dan dimuat per halaman saat digulir; [page] berbasis nol. */
    suspend fun ingredientChoices(query: String, page: Int): DeviceResult<ChoicePage<StockIngredient>> =
        when (val result = ingredients(PageRequest(page = page, query = query, filter = "", params = emptyMap()))) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(ChoicePage(result.value.items, hasMore = page * StockPageSize + result.value.items.size < result.value.total))
        }

    /** Riwayat satu atau beberapa jenis sekaligus, misalnya Rusak dan RnD dalam satu daftar; dicari dari nama bahan atau catatan. */
    suspend fun movements(kinds: Set<MovementKind>, request: PageRequest): DeviceResult<ListPage<StockMovement>> =
        when (
            val result = api.get(
                path = "$StockPath/movements",
                serializer = MovementPageDto.serializer(),
                query = mapOf(
                    "kind" to kinds.map { it.code },
                    "search" to request.query,
                    "page" to request.page + 1,
                    "size" to StockPageSize,
                    "sort" to request.sort,
                    "start" to request.params[ListParam.From],
                    "end" to request.params[ListParam.To],
                    "user_id" to request.params[ListParam.UserId],
                ),
            )
        ) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(ListPage(result.value.items.map { it.toModel() }, result.value.total))
        }

    /** Semua catatan satu bahan di cabang tablet, termasuk penjualan, stok awal, dan penutupan periode, terbaru dulu. */
    suspend fun ingredientMovements(ingredientId: String, request: PageRequest): DeviceResult<ListPage<StockMovement>> =
        when (
            val result = api.get(
                path = "$StockPath/ingredients/$ingredientId/movements",
                serializer = MovementPageDto.serializer(),
                query = mapOf("page" to request.page + 1, "size" to StockPageSize, "user_id" to request.params[ListParam.UserId]),
            )
        ) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(ListPage(result.value.items.map { it.toModel() }, result.value.total))
        }

    /** [qty] berupa besaran tanpa tanda; arah catatan dijaga server. */
    suspend fun correct(movementId: String, qty: String, note: String): DeviceResult<Unit> =
        when (
            val result = api.send(
                method = HttpMethod.Patch,
                path = "$StockPath/movements/$movementId",
                body = buildJsonObject {
                    put("qty", qty)
                    put("note", note.trim())
                },
                serializer = MovementDto.serializer(),
            )
        ) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(Unit)
        }

    suspend fun remove(movementId: String): DeviceResult<Unit> = api.sendUnit(HttpMethod.Delete, "$StockPath/movements/$movementId")

    suspend fun causes(): DeviceResult<List<WasteCause>> =
        when (val result = api.get(path = "$StockPath/causes", serializer = ListSerializer(CauseDto.serializer()))) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(result.value.map { WasteCause(it.code, it.label) })
        }

    suspend fun receive(ingredientId: String, qty: String, note: String, proof: ByteArray?): DeviceResult<EntrySaved> =
        write("receipts", buildJsonObject {
            put("ingredient_id", ingredientId)
            put("qty", qty)
            putText("note", note)
        }, proof)

    suspend fun waste(ingredientId: String, qty: String, cause: String, note: String, proof: ByteArray?): DeviceResult<EntrySaved> =
        write("waste", buildJsonObject {
            put("ingredient_id", ingredientId)
            put("qty", qty)
            put("cause", cause)
            putText("note", note)
        }, proof)

    suspend fun trial(ingredientId: String, qty: String, note: String): DeviceResult<EntrySaved> =
        write("trials", buildJsonObject {
            put("ingredient_id", ingredientId)
            put("qty", qty)
            put("note", note.trim())
        }, null)

    /** Melampirkan atau mengganti foto nota atau bukti satu catatan; foto dikonversi di perangkat sebelum dikirim. */
    suspend fun attachProof(movementId: String, image: ByteArray): DeviceResult<Unit> =
        when (val result = api.upload("$StockPath/movements/$movementId/proof", "file", image, MovementDto.serializer())) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(Unit)
        }

    suspend fun openingPeriod(): DeviceResult<OpeningPeriod> =
        when (val result = api.get(path = "$StockPath/opening-period", serializer = OpeningPeriodDto.serializer())) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(result.value.toModel())
        }

    suspend fun journey(ingredientId: String): DeviceResult<StockJourney> =
        when (val result = api.get(path = "$StockPath/ingredients/$ingredientId/journey", serializer = JourneyDto.serializer())) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(result.value.toModel())
        }

    /** [qty] adalah stok awal yang sudah dirapikan; server mencatat selisihnya terhadap stok sebelum periode. */
    suspend fun setOpening(ingredientId: String, qty: String): DeviceResult<StockJourney> =
        when (
            val result = api.send(
                method = HttpMethod.Put,
                path = "$StockPath/ingredients/$ingredientId/opening",
                body = buildJsonObject { put("qty", qty) },
                serializer = JourneyDto.serializer(),
            )
        ) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(result.value.toModel())
        }


    /** Mengisi stok awal banyak bahan sekaligus; setiap baris berhasil atau gagal sendiri, dengan alasan dari server. */
    suspend fun setOpenings(rows: List<OpeningRow>): DeviceResult<List<OpeningRowResult>> =
        when (
            val result = api.send(
                method = HttpMethod.Post,
                path = "$StockPath/openings/bulk",
                body = buildJsonObject {
                    putJsonArray("items") {
                        rows.forEach { row ->
                            add(buildJsonObject {
                                put("ingredient_id", row.ingredientId)
                                put("qty", row.qty)
                            })
                        }
                    }
                },
                serializer = BulkResultDto.serializer(),
            )
        ) {
            is DeviceResult.Failed -> result
            // Nomor baris dari server berbasis satu dan urut sama dengan kiriman.
            is DeviceResult.Ok -> DeviceResult.Ok(result.value.results.mapNotNull { row -> rows.getOrNull(row.row - 1)?.let { OpeningRowResult(it.ingredientId, row.error.takeIf { !row.ok }) } })
        }

    suspend fun removeOpening(ingredientId: String): DeviceResult<StockJourney> =
        when (
            val result = api.send(
                method = HttpMethod.Delete,
                path = "$StockPath/ingredients/$ingredientId/opening",
                body = null,
                serializer = JourneyDto.serializer(),
            )
        ) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(result.value.toModel())
        }

    suspend fun recipeUses(ingredientId: String, request: PageRequest): DeviceResult<ListPage<RecipeUse>> =
        when (
            val result = api.get(
                path = "$StockPath/ingredients/$ingredientId/recipes",
                serializer = RecipeUsePageDto.serializer(),
                query = mapOf("page" to request.page + 1, "size" to StockPageSize),
            )
        ) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(ListPage(result.value.items.map { RecipeUse(it.menuId, it.menuName, it.qty) }, result.value.total))
        }

    /** Admin yang menutup periode di web; tablet hanya mengajukan. */
    suspend fun requestClose(note: String): DeviceResult<Unit> =
        when (
            val result = api.send(
                method = HttpMethod.Post,
                path = "$StockPath/close-requests",
                body = buildJsonObject { putText("note", note) },
                serializer = RequestDto.serializer(),
            )
        ) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(Unit)
        }

    // Catatan disimpan dulu, baru fotonya; foto yang gagal tidak membatalkan catatan supaya tidak tercatat dua kali saat diulang.
    private suspend fun write(route: String, body: kotlinx.serialization.json.JsonElement, proof: ByteArray?): DeviceResult<EntrySaved> =
        when (val result = api.send(method = HttpMethod.Post, path = "$StockPath/$route", body = body, serializer = MovementDto.serializer())) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> {
                val id = result.value.id
                val saved = proof == null || attachProof(id, proof) is DeviceResult.Ok
                DeviceResult.Ok(EntrySaved(id, saved))
            }
        }
}

@Serializable
private class IngredientDto(
    val id: String,
    val name: String,
    val unit: String? = null,
    val category: String? = null,
    val stock: String = "0",
    val minimum: String = "0",
    val opening: String? = null,
    @SerialName("package_size") val packageSize: String = "1",
) {
    fun toModel() = StockIngredient(id, name, unit, category, stock, minimum, opening, packageSize)
}

@Serializable
private class IngredientPageDto(val items: List<IngredientDto>, val total: Int)

@Serializable
private class MovementDto(
    val id: String,
    @SerialName("ingredient_name") val ingredientName: String = "",
    val unit: String? = null,
    val qty: String = "0",
    val kind: String = "",
    @SerialName("cause_label") val causeLabel: String? = null,
    val note: String? = null,
    @SerialName("user_name") val userName: String? = null,
    @SerialName("created_at") val createdAt: String = "",
    @SerialName("from_sale") val fromSale: Boolean = false,
    @SerialName("from_count") val fromCount: Boolean = false,
    @SerialName("from_opening") val fromOpening: Boolean = false,
    @SerialName("proof_url") val proofUrl: String? = null,
) {
    fun toModel() = StockMovement(id, ingredientName, unit, qty, CardKind.of(kind), causeLabel, note, userName, createdAt, fromSale, fromCount, fromOpening, proofUrl)
}

@Serializable
private class MovementPageDto(val items: List<MovementDto>, val total: Int)

@Serializable
private class CauseDto(val code: String, val label: String)

@Serializable
private class RequestDto(
    val status: String,
    val note: String? = null,
    @SerialName("requested_by") val requestedBy: String? = null,
    @SerialName("created_at") val createdAt: String = "",
    @SerialName("decided_by") val decidedBy: String? = null,
    @SerialName("decided_at") val decidedAt: String? = null,
) {
    /** Status yang belum dikenal app versi ini dibaca sebagai menunggu, supaya tablet tidak mengajukan ganda. */
    fun toModel() = CloseRequest(
        status = when (status) {
            "rejected" -> CloseRequestStatus.Rejected
            "closed" -> CloseRequestStatus.Closed
            else -> CloseRequestStatus.Pending
        },
        note = note,
        requestedBy = requestedBy,
        createdAt = createdAt,
        decidedBy = decidedBy,
        decidedAt = decidedAt,
    )
}

@Serializable
private class OpeningPeriodDto(
    val start: String,
    @SerialName("close_start") val closeStart: String = "",
    @SerialName("close_end") val closeEnd: String = "",
    val filled: Int = 0,
    val total: Int = 0,
    val request: RequestDto? = null,
) {
    // Server lama tanpa rentang tutup: awal periode berjalan sampai hari ini.
    fun toModel() = OpeningPeriod(start, closeStart.ifEmpty { start }, closeEnd.ifEmpty { BusinessDay.today() }, filled, total, request?.toModel())
}

@Serializable
private class JourneyDto(
    val start: String,
    val opening: String = "0",
    @SerialName("opening_set") val openingSet: Boolean = false,
    @SerialName("opening_by") val openingBy: String? = null,
    @SerialName("opening_at") val openingAt: String? = null,
    val received: String = "0",
    val sold: String = "0",
    val wasted: String = "0",
    val trial: String = "0",
    val adjusted: String = "0",
    val stock: String = "0",
) {
    fun toModel() = StockJourney(start, opening, openingSet, openingBy, openingAt, received, sold, wasted, trial, adjusted, stock)
}

@Serializable
private class RecipeUseDto(
    @SerialName("menu_item_id") val menuId: String,
    @SerialName("menu_name") val menuName: String,
    val qty: String = "0",
)

@Serializable
private class RecipeUsePageDto(val items: List<RecipeUseDto>, val total: Int)
