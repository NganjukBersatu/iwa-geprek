package id.kongstudio.cafe.feature.devicesetup

import kotlinx.serialization.Serializable

/** Identitas perangkat operasional dari server; [token] dipakai sebagai Bearer, jadi harus dijaga. */
@Serializable
class DeviceCredential(
    val id: String,
    val token: String,
    val name: String,
    val section: String,
    /** Sudah pernah dipindai karyawan; bertahan sampai perangkat dilepas, seperti sesi login. */
    val linked: Boolean = false,
    /** Karyawan yang memindai QR; tablet bertindak atas namanya dengan [userToken]. */
    val userName: String? = null,
    val userToken: String? = null,
)

/** Identitas yang dilaporkan perangkat saat pairing; kolom yang tidak terbaca dikirim null. */
class DeviceInfo(
    val androidId: String?,
    val serial: String?,
    val brand: String?,
    val model: String?,
)

/** Penyimpan permanen status perangkat operasional; tidak kedaluwarsa sampai dilepas. */
interface DeviceModeStore {
    suspend fun load(): DeviceCredential?

    /** [code] hanya disimpan sebagai hash, untuk pelepasan lewat kode di perangkat itu. */
    suspend fun save(credential: DeviceCredential, code: String)

    /** Benar bila [code] sama dengan kode saat perangkat didaftarkan. */
    suspend fun matches(code: String): Boolean

    /** Menandai perangkat sudah terhubung ke karyawan agar tidak meminta pindai ulang. */
    suspend fun markLinked(userName: String?, userToken: String?)

    /** Melepas karyawan yang tertaut tanpa melepas perangkat; QR tampil lagi untuk pindai ulang. */
    suspend fun markUnlinked()

    suspend fun clear()

    fun deviceInfo(): DeviceInfo
}
