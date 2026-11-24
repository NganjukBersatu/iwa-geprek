package id.kongstudio.cafe.feature.permission

import kotlinx.coroutines.flow.StateFlow

enum class PermissionKind { Location, Camera, Gps, Bluetooth }

/** Untuk apa gerbang izin dibuka; menentukan izin yang diminta, urutan barisnya = urutan [kinds]. */
enum class PermissionPurpose(val kinds: List<PermissionKind>) {
    Attendance(listOf(PermissionKind.Location, PermissionKind.Camera, PermissionKind.Gps)),
    Operational(listOf(PermissionKind.Camera, PermissionKind.Bluetooth)),
}

enum class PermissionStatus { Granted, Denied }

/** Jembatan ke izin dan layanan perangkat; implementasinya diberikan oleh platform. */
interface DevicePermissions {
    val status: StateFlow<Map<PermissionKind, PermissionStatus>>

    /** Membaca ulang status, misalnya saat aplikasi kembali aktif. */
    fun refresh()

    /** Menampilkan dialog sistem untuk [kind]; selesai setelah pengguna menjawab. */
    suspend fun request(kind: PermissionKind)
}
