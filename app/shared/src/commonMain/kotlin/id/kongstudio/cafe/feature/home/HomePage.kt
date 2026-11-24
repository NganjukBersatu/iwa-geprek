package id.kongstudio.cafe.feature.home

import androidx.compose.ui.graphics.vector.ImageVector
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.nav_activity
import id.kongstudio.cafe.resources.nav_attendance
import id.kongstudio.cafe.resources.nav_dashboard
import id.kongstudio.cafe.resources.nav_info
import id.kongstudio.cafe.resources.nav_leave_overtime
import id.kongstudio.cafe.resources.nav_more
import id.kongstudio.cafe.resources.nav_performance
import id.kongstudio.cafe.resources.nav_presence
import id.kongstudio.cafe.resources.nav_profile
import id.kongstudio.cafe.resources.nav_schedule
import id.kongstudio.cafe.resources.nav_sop
import id.kongstudio.cafe.resources.nav_tasks
import id.kongstudio.cafe.ui.component.featurecard.CardTone
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.StringResource

internal enum class HomePage(val label: StringResource, val icon: ImageVector) {
    Dashboard(Res.string.nav_dashboard, AppIcons.Dashboard),
    Schedule(Res.string.nav_schedule, AppIcons.Calendar),
    Attendance(Res.string.nav_attendance, AppIcons.CalendarCheck),
    Tasks(Res.string.nav_tasks, AppIcons.Checklist),
    Profile(Res.string.nav_profile, AppIcons.UserCircle),
    Sop(Res.string.nav_sop, AppIcons.Book),
    Info(Res.string.nav_info, AppIcons.Info),
    LeaveOvertime(Res.string.nav_leave_overtime, AppIcons.Briefcase),
    Performance(Res.string.nav_performance, AppIcons.Dashboard),
    Presence(Res.string.nav_presence, AppIcons.Calendar),
    Activity(Res.string.nav_activity, AppIcons.History),
    More(Res.string.nav_more, AppIcons.More),
}

/** Tujuan utama di bilah bawah dan rail; Absen di tengah dan paling menonjol. */
internal val HomeTabs = listOf(
    HomePage.Dashboard,
    HomePage.Schedule,
    HomePage.Attendance,
    HomePage.Profile,
    HomePage.More,
)

/** Halaman yang dibuka dari Lainnya; tab Lainnya tetap menyala selama salah satunya terbuka. */
internal val HomeMoreEntries = listOf(
    HomePage.Tasks,
    HomePage.Sop,
    HomePage.Info,
    HomePage.LeaveOvertime,
    HomePage.Performance,
    HomePage.Presence,
    HomePage.Activity,
)

/** Satu kartu di halaman Lainnya; [target] adalah halaman yang dibuka, boleh sebuah tab. */
internal class MoreCard(
    val target: HomePage,
    val title: StringResource,
    val icon: ImageVector,
    val decoration: ImageVector,
    val tone: CardTone,
)

/** Urutan kartu Lainnya, dua kolom: baris pertama Tugas dan Kinerja, lalu Kehadiran dan Izin & Lembur, Riwayat dan Prosedur Kerja, terakhir Info Aplikasi di tengah. */
internal val HomeMoreCards = listOf(
    MoreCard(HomePage.Tasks, Res.string.nav_tasks, AppIcons.Checklist, AppIcons.ClipboardCheck, CardTone.Primary),
    MoreCard(HomePage.Performance, Res.string.nav_performance, AppIcons.Dashboard, AppIcons.ChartLine, CardTone.Deep),
    MoreCard(HomePage.Presence, Res.string.nav_presence, AppIcons.Calendar, AppIcons.CalendarCheck, CardTone.Soft),
    MoreCard(HomePage.LeaveOvertime, Res.string.nav_leave_overtime, AppIcons.Briefcase, AppIcons.Moon, CardTone.Primary),
    MoreCard(HomePage.Activity, Res.string.nav_activity, AppIcons.History, AppIcons.ClipboardList, CardTone.Accent),
    MoreCard(HomePage.Sop, Res.string.nav_sop, AppIcons.Book, AppIcons.FileText, CardTone.Soft),
    MoreCard(HomePage.Info, Res.string.nav_info, AppIcons.Info, AppIcons.HelpCircle, CardTone.Primary),
)
