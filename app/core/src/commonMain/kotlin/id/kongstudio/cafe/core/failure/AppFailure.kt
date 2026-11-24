package id.kongstudio.cafe.core.failure

/** Satu-satunya daftar sebab gagal di aplikasi; teksnya hanya di [failureText] dan [where] berisi metode serta alamat yang gagal. */
sealed interface AppFailure {
    /** Server tidak terjangkau: tanpa jaringan, nama server tidak ditemukan, atau sambungan ditolak. */
    data class Unreachable(val where: String) : AppFailure

    /** Sambungan terjalin tetapi server tidak menjawab tepat waktu. */
    data class Timeout(val where: String) : AppFailure

    /** Sertifikat atau jabat tangan aman gagal; biasanya tanggal dan jam perangkat salah. */
    data class SecureConnection(val where: String) : AppFailure

    /** Kesalahan di dalam aplikasi sendiri; [kind] adalah jenis exception supaya bisa dilacak. */
    data class Unexpected(val kind: String, val where: String) : AppFailure

    /** Server menjawab 5xx, atau jawabannya tidak bisa dibaca. */
    data class Server(val code: Int, val where: String) : AppFailure

    /** 404 atau 405: server yang berjalan tidak punya alamat ini. */
    data class NotFound(val code: Int, val where: String) : AppFailure

    /** Ditolak server (4xx selain 401 dan 404); [message] dari backend bila ada, dan [serverCode] kode galat stabil dari badan jawabannya. */
    data class Rejected(val code: Int, val message: String?, val serverCode: String? = null) : AppFailure

    /** Token karyawan ditolak server. */
    data object Unauthorized : AppFailure
}

/** True bila server tidak bisa dicapai sehingga pekerjaan boleh disimpan dulu dan dikirim ulang nanti. */
val AppFailure.isOffline: Boolean
    get() = this is AppFailure.Unreachable || this is AppFailure.Timeout || this is AppFailure.SecureConnection
