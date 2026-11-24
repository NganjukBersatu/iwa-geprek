package id.kongstudio.cafe.feature.ordernotes

import id.kongstudio.cafe.feature.admin.AdminApi
import id.kongstudio.cafe.feature.admin.ListPage
import id.kongstudio.cafe.feature.admin.ListParam
import id.kongstudio.cafe.feature.admin.PageRequest
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import io.ktor.http.HttpMethod
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

// Tabel yang perubahannya membuat layar ini memuat ulang; namanya sama dengan nama tabel di backend.
internal val OrderNoteTables = setOf("categories")

internal const val OrderNotePageSize = 30
private const val NotesPath = "/v2/operational/order-notes"

/** [shared] menandai catatan umum lama yang berlaku di semua cabang dan hanya bisa diatur dari web admin; [createdBy] kosong untuk catatan lama. */
internal class OrderNote(val id: String, val name: String, val usedBy: Int, val shared: Boolean, val createdBy: String?)

/** Catatan pesanan milik cabang tablet ini: dipilih di kasir, diatur di sini. */
internal class OrderNoteRepository(private val api: AdminApi) {
    suspend fun list(request: PageRequest): DeviceResult<ListPage<OrderNote>> =
        when (
            val result = api.get(
                path = "$NotesPath/manage",
                serializer = NotePageDto.serializer(),
                query = mapOf(
                    "page" to request.page + 1,
                    "size" to OrderNotePageSize,
                    "search" to request.query,
                    "sort" to request.sort,
                    "created_by_id" to request.params[ListParam.UserId],
                ),
            )
        ) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(ListPage(result.value.items.map { it.toModel() }, result.value.total))
        }

    suspend fun create(name: String): DeviceResult<Unit> =
        api.sendUnit(method = HttpMethod.Post, path = "$NotesPath/manage", body = buildJsonObject { put("name", name.trim()) })

    suspend fun rename(note: OrderNote, name: String): DeviceResult<Unit> =
        api.sendUnit(method = HttpMethod.Patch, path = "$NotesPath/manage/${note.id}", body = buildJsonObject { put("name", name.trim()) })

    suspend fun delete(note: OrderNote): DeviceResult<Unit> = api.sendUnit(method = HttpMethod.Delete, path = "$NotesPath/manage/${note.id}")
}

@Serializable
private class NoteDto(
    val id: String,
    val name: String,
    @SerialName("used_by_orders") val usedByOrders: Int = 0,
    val shared: Boolean = false,
    @SerialName("created_by") val createdBy: String? = null,
) {
    fun toModel() = OrderNote(id, name, usedByOrders, shared, createdBy)
}

@Serializable
private class NotePageDto(val items: List<NoteDto>, val total: Int)
