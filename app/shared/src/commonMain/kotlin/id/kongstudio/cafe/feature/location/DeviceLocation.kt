package id.kongstudio.cafe.feature.location

/** Satu pembacaan posisi perangkat; [accuracyMeters] adalah radius ketidakpastiannya. */
class LocationFix(val latitude: Double, val longitude: Double, val accuracyMeters: Float)

/** Jembatan ke posisi perangkat; implementasinya diberikan oleh platform. */
interface DeviceLocation {
    /** Posisi terkini, atau null bila izin belum ada atau posisi tidak terbaca tepat waktu. */
    suspend fun current(): LocationFix?

    /** Jarak garis lurus dalam meter dari [fix] ke titik [latitude], [longitude], dihitung platform. */
    fun distanceMeters(fix: LocationFix, latitude: Double, longitude: Double): Double
}
