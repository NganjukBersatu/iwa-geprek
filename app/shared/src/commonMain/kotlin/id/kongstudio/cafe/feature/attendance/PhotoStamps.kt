package id.kongstudio.cafe.feature.attendance

import androidx.compose.ui.graphics.toArgb
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.image.PhotoStamp
import id.kongstudio.cafe.core.image.StampLine
import id.kongstudio.cafe.core.time.ServerClock
import id.kongstudio.cafe.feature.location.DeviceLocation
import id.kongstudio.cafe.feature.location.LocationFix
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.attendance_stamp_branch
import id.kongstudio.cafe.resources.attendance_stamp_coordinates
import id.kongstudio.cafe.resources.attendance_stamp_date
import id.kongstudio.cafe.resources.attendance_stamp_distance
import id.kongstudio.cafe.resources.attendance_stamp_inside
import id.kongstudio.cafe.resources.attendance_stamp_name
import id.kongstudio.cafe.resources.attendance_stamp_outside
import id.kongstudio.cafe.resources.attendance_stamp_time
import id.kongstudio.cafe.resources.format_date_plain
import id.kongstudio.cafe.resources.months
import id.kongstudio.cafe.ui.theme.color.LightAppColors
import kotlin.math.abs
import kotlin.math.roundToInt
import kotlin.math.roundToLong
import org.jetbrains.compose.resources.getString
import org.jetbrains.compose.resources.getStringArray

private const val COORDINATE_SCALE = 1_000_000L
private const val COORDINATE_DIGITS = 6

/** Isi cap foto absen, sama dengan PWA: jam, tanggal, nama, cabang, koordinat, jarak, dan lokasi absen. */
internal object PhotoStamps {
    suspend fun build(
        userName: String,
        branch: AttendanceBranch?,
        fix: LocationFix,
        location: DeviceLocation,
        outside: Boolean,
        note: String?,
    ): PhotoStamp {
        val now = DateTimeFormat.stampAt(ServerClock.nowEpochSeconds())
        val months = getStringArray(Res.array.months)
        val date = getString(
            Res.string.format_date_plain,
            DateTimeFormat.dayOfMonth(now.date),
            months[DateTimeFormat.monthIndex(now.date)],
            now.date.take(4),
        )
        val lines = buildList {
            add(StampLine(getString(Res.string.attendance_stamp_time, now.time), bold = true))
            add(StampLine(getString(Res.string.attendance_stamp_date, date), bold = true))
            add(StampLine(getString(Res.string.attendance_stamp_name, userName)))
            branch?.let { add(StampLine(getString(Res.string.attendance_stamp_branch, it.name))) }
            add(
                StampLine(
                    getString(
                        Res.string.attendance_stamp_coordinates,
                        coordinate(fix.latitude),
                        coordinate(fix.longitude),
                        fix.accuracyMeters.roundToInt().toString(),
                    ),
                ),
            )
            val latitude = branch?.latitude
            val longitude = branch?.longitude
            val radius = branch?.radiusMeters
            if (latitude != null && longitude != null && radius != null) {
                val meters = location.distanceMeters(fix, latitude, longitude).roundToInt()
                add(StampLine(getString(Res.string.attendance_stamp_distance, meters.toString(), radius.toString())))
            }
            add(
                if (outside) {
                    StampLine(getString(Res.string.attendance_stamp_outside, note.orEmpty()), bold = true)
                } else {
                    StampLine(getString(Res.string.attendance_stamp_inside))
                },
            )
        }
        return PhotoStamp(lines, LightAppColors.scrim.toArgb(), LightAppColors.onPrimary.toArgb())
    }

    /** Koordinat dengan enam angka di belakang koma, seperti di PWA. */
    private fun coordinate(value: Double): String {
        val scaled = (value * COORDINATE_SCALE).roundToLong()
        val sign = if (scaled < 0) "-" else ""
        val whole = abs(scaled) / COORDINATE_SCALE
        val fraction = (abs(scaled) % COORDINATE_SCALE).toString().padStart(COORDINATE_DIGITS, '0')
        return "$sign$whole.$fraction"
    }
}
