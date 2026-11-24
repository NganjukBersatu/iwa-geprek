package id.kongstudio.cafe.feature.deposits

/** Hari bisnis sebuah cabang beserta uang yang sudah disetor untuk hari itu (0 bila belum ada). */
internal class DayState(val outletId: String, val day: String, val deposited: Long, val unfinished: Boolean)

/** Pemeriksaan hari setoran sebelum uang diubah; tombol lanjut menunggu sampai jawabannya ada. */
internal sealed interface DayCheck {
    data object Idle : DayCheck

    data object Checking : DayCheck

    class Ready(val days: List<DayState>) : DayCheck {
        val deposited: List<DayState> get() = days.filter { it.deposited > 0 }
    }

    data object Failed : DayCheck
}
