package id.kongstudio.cafe.feature.visitorcategories

import id.kongstudio.cafe.feature.admin.AdminApi
import id.kongstudio.cafe.feature.admin.ListPage
import id.kongstudio.cafe.feature.admin.PageRequest
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import io.ktor.http.HttpMethod
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

// Tabel yang perubahannya membuat layar ini memuat ulang; namanya sama dengan nama tabel di backend.
internal val VisitorOptionTables = setOf("visitor_categories", "visitor_genders")

/** Daftarnya tidak berhalaman, jadi satu halaman besar memuat semuanya. */
internal const val VisitorOptionPageSize = 100

internal const val SectionCategory = "kategori"
internal const val SectionGender = "gender"
private const val VisitorsPath = "/v2/operational/visitors"

private fun pathOf(section: String) = if (section == SectionGender) "$VisitorsPath/genders" else "$VisitorsPath/categories"

/** Satu pilihan yang dipilih kasir saat mencatat pesanan: kategori pengunjung atau gender. */
internal class VisitorOption(
    val id: String,
    val name: String,
    val active: Boolean,
    val asksGender: Boolean,
    val usedBy: Int,
    val section: String,
)

internal class VisitorOptionRepository(private val api: AdminApi) {
    suspend fun list(request: PageRequest): DeviceResult<ListPage<VisitorOption>> {
        val section = request.filter.ifEmpty { SectionCategory }
        return when (val result = api.get(pathOf(section), ListSerializer(OptionDto.serializer()))) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(
                result.value.map { it.toModel(section) }.let { ListPage(it, it.size) },
            )
        }
    }

    suspend fun create(section: String, name: String, asksGender: Boolean): DeviceResult<Unit> = api.sendUnit(
        method = HttpMethod.Post,
        path = pathOf(section),
        body = buildJsonObject {
            put("name", name.trim())
            put("is_active", true)
            if (section == SectionCategory) put("asks_gender", asksGender)
        },
    )

    suspend fun update(option: VisitorOption, name: String, asksGender: Boolean, active: Boolean): DeviceResult<Unit> =
        api.sendUnit(
            method = HttpMethod.Put,
            path = "${pathOf(option.section)}/${option.id}",
            body = buildJsonObject {
                put("name", name.trim())
                put("is_active", active)
                if (option.section == SectionCategory) put("asks_gender", asksGender)
            },
        )

    suspend fun delete(option: VisitorOption): DeviceResult<Unit> =
        api.sendUnit(HttpMethod.Delete, "${pathOf(option.section)}/${option.id}")
}

@Serializable
private class OptionDto(
    val id: String,
    val name: String,
    @SerialName("is_active") val active: Boolean = true,
    @SerialName("asks_gender") val asksGender: Boolean = false,
    @SerialName("used_by") val usedBy: Int = 0,
) {
    fun toModel(section: String) = VisitorOption(id, name, active, asksGender, usedBy, section)
}
