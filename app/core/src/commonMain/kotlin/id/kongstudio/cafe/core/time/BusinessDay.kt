package id.kongstudio.cafe.core.time

import id.kongstudio.cafe.core.format.DateTimeFormat
import kotlin.concurrent.Volatile

/** Keadaan sesi kasir perangkat ini menurut server: berjalan dengan hari bisnisnya, atau tidak ada. */
sealed interface ShiftDay {
    data object None : ShiftDay

    data class Running(val day: String) : ShiftDay
}

/** Satu-satunya sumber "hari ini" untuk uang, promo, dan sesi: hari bisnis sesi yang berjalan, atau tanggal WIB jam server bila tidak ada sesi. */
object BusinessDay {
    @Volatile
    private var shift: ShiftDay = ShiftDay.None

    fun today(): String = when (val current = shift) {
        is ShiftDay.Running -> current.day
        ShiftDay.None -> DateTimeFormat.todayWib()
    }

    fun follow(next: ShiftDay) {
        shift = next
    }
}
