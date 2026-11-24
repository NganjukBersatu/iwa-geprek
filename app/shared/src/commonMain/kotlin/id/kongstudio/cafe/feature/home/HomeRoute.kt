package id.kongstudio.cafe.feature.home

import id.kongstudio.cafe.resources.back_to_page
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.feature.about.AboutPage
import id.kongstudio.cafe.feature.activity.ActivityRoute
import id.kongstudio.cafe.feature.attendance.AttendanceRoute
import id.kongstudio.cafe.feature.attendancelog.AttendanceLogRoute
import id.kongstudio.cafe.feature.auth.session.LoginSession
import id.kongstudio.cafe.feature.dashboard.DashboardRoute
import id.kongstudio.cafe.feature.location.DeviceLocation
import id.kongstudio.cafe.feature.network.NetworkGate
import id.kongstudio.cafe.feature.network.NetworkMonitor
import id.kongstudio.cafe.feature.notices.NoticeRoute
import id.kongstudio.cafe.feature.leaveovertime.LeaveOvertimeRoute
import id.kongstudio.cafe.feature.pairing.PairingSection
import id.kongstudio.cafe.feature.performance.PerformanceRoute
import id.kongstudio.cafe.feature.profile.ProfileRoute
import id.kongstudio.cafe.feature.schedule.ScheduleRoute
import id.kongstudio.cafe.feature.sop.SopRoute
import id.kongstudio.cafe.feature.tasks.TaskRoute
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.brand_logo
import id.kongstudio.cafe.resources.nav_logout
import id.kongstudio.cafe.resources.shell_logo_description
import id.kongstudio.cafe.resources.shell_rail_collapse
import id.kongstudio.cafe.resources.shell_rail_expand
import id.kongstudio.cafe.resources.shell_rail_subtitle
import id.kongstudio.cafe.resources.shell_rail_title
import id.kongstudio.cafe.ui.component.appshell.AppShell
import id.kongstudio.cafe.ui.component.backhandler.PlatformBackHandler
import id.kongstudio.cafe.ui.component.bottombar.AppBottomBar
import id.kongstudio.cafe.ui.component.bottombar.BottomBarItem
import id.kongstudio.cafe.ui.component.sidebarheader.SidebarHeader
import id.kongstudio.cafe.ui.component.sidebaritem.SidebarItem
import id.kongstudio.cafe.ui.component.subpageheader.HeaderBack
import id.kongstudio.cafe.ui.component.subpageheader.SubPageHeader
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import io.ktor.client.HttpClient
import org.jetbrains.compose.resources.painterResource
import org.jetbrains.compose.resources.stringResource

@Composable
fun HomeRoute(
    session: LoginSession,
    client: HttpClient,
    location: DeviceLocation,
    network: NetworkMonitor,
    onLogout: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var pageName by rememberSaveable { mutableStateOf(HomePage.Dashboard.name) }
    val page = HomePage.valueOf(pageName)

    // Kehadiran bisa dibuka dari Dashboard maupun Lainnya; kembali selalu ke halaman asalnya.
    var presenceFrom by rememberSaveable { mutableStateOf(HomePage.More.name) }
    val presenceOrigin = HomePage.valueOf(presenceFrom)

    // Halaman dari Lainnya tetap menyalakan tab Lainnya dan kembali ke daftarnya.
    val activeTab = when {
        page == HomePage.Presence -> presenceOrigin
        page in HomeMoreEntries -> HomePage.More
        else -> page
    }
    val backTarget = when {
        page == HomePage.Presence -> presenceOrigin
        page in HomeMoreEntries -> HomePage.More
        else -> HomePage.Dashboard
    }

    PlatformBackHandler(enabled = page != HomePage.Dashboard) { pageName = backTarget.name }

    NoticeRoute(session = session, client = client, onSessionExpired = onLogout)

    AppShell(
        modifier = modifier,
        bottomBar = {
            AppBottomBar(
                items = HomeTabs.map { tab ->
                    BottomBarItem(
                        label = stringResource(tab.label),
                        icon = tab.icon,
                        selected = tab == activeTab,
                        onClick = { pageName = tab.name },
                        prominent = tab == HomePage.Attendance,
                    )
                },
            )
        },
        rail = { collapsed, onToggle ->
            SidebarHeader(
                logo = painterResource(Res.drawable.brand_logo),
                logoDescription = stringResource(Res.string.shell_logo_description),
                title = stringResource(Res.string.shell_rail_title),
                subtitle = stringResource(Res.string.shell_rail_subtitle),
                collapsed = collapsed,
                onToggleCollapsed = onToggle,
                collapseDescription = stringResource(Res.string.shell_rail_collapse),
                expandDescription = stringResource(Res.string.shell_rail_expand),
            )
            Column(modifier = Modifier.weight(1f)) {
                HomeTabs.forEach { tab ->
                    SidebarItem(
                        label = stringResource(tab.label),
                        icon = tab.icon,
                        selected = tab == activeTab,
                        collapsed = collapsed,
                        onClick = { pageName = tab.name },
                    )
                }
            }
            SidebarItem(
                label = stringResource(Res.string.nav_logout),
                icon = AppIcons.Logout,
                selected = false,
                collapsed = collapsed,
                onClick = onLogout,
            )
        },
    ) {
        NetworkGate(network, blocking = true) {
            when (page) {
                HomePage.Dashboard -> DashboardRoute(
                    session = session,
                    client = client,
                    onSessionExpired = onLogout,
                    onOpenAttendance = {
                        presenceFrom = HomePage.Dashboard.name
                        pageName = HomePage.Presence.name
                    },
                )
                HomePage.Schedule -> ScheduleRoute(session = session, client = client, onSessionExpired = onLogout)
                HomePage.Attendance -> AttendanceRoute(
                    session = session,
                    client = client,
                    location = location,
                    onSessionExpired = onLogout,
                ) {
                    PairingSection(session = session, client = client, onSessionExpired = onLogout)
                }
                HomePage.More -> MorePage(cards = HomeMoreCards, onSelect = {
                    if (it == HomePage.Presence) presenceFrom = HomePage.More.name
                    pageName = it.name
                })
                HomePage.Tasks -> SubPage(
                    title = stringResource(page.label),
                    onBack = { pageName = HomePage.More.name },
                    backTo = HomePage.More,
                ) {
                    TaskRoute(session = session, client = client, onSessionExpired = onLogout)
                }
                HomePage.Sop -> SubPage(
                    title = stringResource(page.label),
                    onBack = { pageName = HomePage.More.name },
                    backTo = HomePage.More,
                ) {
                    SopRoute(session = session, client = client, onSessionExpired = onLogout)
                }
                HomePage.LeaveOvertime -> SubPage(
                    title = stringResource(page.label),
                    onBack = { pageName = HomePage.More.name },
                    backTo = HomePage.More,
                ) {
                    LeaveOvertimeRoute(session = session, client = client, onSessionExpired = onLogout)
                }
                HomePage.Performance -> SubPage(
                    title = stringResource(page.label),
                    onBack = { pageName = HomePage.More.name },
                    backTo = HomePage.More,
                ) {
                    PerformanceRoute(session = session, client = client, onSessionExpired = onLogout)
                }
                HomePage.Presence -> SubPage(
                    title = stringResource(page.label),
                    onBack = { pageName = backTarget.name },
                    backTo = backTarget,
                ) {
                    AttendanceLogRoute(session = session, client = client, onSessionExpired = onLogout)
                }
                HomePage.Activity -> SubPage(
                    title = stringResource(page.label),
                    onBack = { pageName = HomePage.More.name },
                    backTo = HomePage.More,
                ) {
                    ActivityRoute(session = session, client = client, onSessionExpired = onLogout)
                }
                HomePage.Info -> SubPage(
                    title = stringResource(page.label),
                    onBack = { pageName = HomePage.More.name },
                    backTo = HomePage.More,
                ) {
                    AboutPage()
                }
                HomePage.Profile -> ProfileRoute(session = session, client = client, onLogout = onLogout)
            }
        }
    }
}

/** Halaman turunan Lainnya: baris judul dengan tombol kembali di atas isi halaman. */
@Composable
private fun SubPage(
    title: String,
    onBack: () -> Unit,
    backTo: HomePage,
    content: @Composable () -> Unit,
) {
    Column(modifier = Modifier.fillMaxSize()) {
        SubPageHeader(title = title, back = HeaderBack(stringResource(Res.string.back_to_page, stringResource(backTo.label)), onBack))
        Box(modifier = Modifier.weight(1f)) { content() }
    }
}
