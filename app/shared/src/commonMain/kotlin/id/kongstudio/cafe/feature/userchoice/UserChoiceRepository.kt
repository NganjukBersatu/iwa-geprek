package id.kongstudio.cafe.feature.userchoice

import id.kongstudio.cafe.feature.admin.AdminApi
import id.kongstudio.cafe.feature.admin.ChoicePage
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.builtins.ListSerializer

private const val ChoicesPath = "/v2/operational/user-choices"
private const val ChoicePageSize = 30

/** Satu orang yang bisa dipilih di penyaring "Dicatat oleh"; [active] salah untuk karyawan yang sudah nonaktif. */
internal class UserChoice(val id: String, val name: String, val outletName: String?, val active: Boolean)

/** Daftar orang dicari dan dimuat per halaman di server, sehingga tidak ada yang terpotong berapa pun jumlah karyawannya. */
internal class UserChoiceRepository(private val api: AdminApi) {
    /** [page] berbasis nol. */
    suspend fun choices(query: String, page: Int): DeviceResult<ChoicePage<UserChoice>> =
        when (
            val result = api.get(
                path = ChoicesPath,
                serializer = ListSerializer(UserChoiceDto.serializer()),
                query = mapOf("search" to query, "page" to page + 1, "size" to ChoicePageSize),
            )
        ) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(
                ChoicePage(result.value.map { UserChoice(it.id, it.name, it.outletName, it.active) }, hasMore = result.value.size == ChoicePageSize),
            )
        }
}

@Serializable
private class UserChoiceDto(
    val id: String,
    val name: String,
    @SerialName("outlet_name") val outletName: String? = null,
    @SerialName("is_active") val active: Boolean = true,
)
