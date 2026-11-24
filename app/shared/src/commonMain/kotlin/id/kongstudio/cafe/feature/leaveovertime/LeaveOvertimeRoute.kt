package id.kongstudio.cafe.feature.leaveovertime

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.lifecycle.compose.LifecycleResumeEffect
import androidx.lifecycle.viewmodel.compose.viewModel
import id.kongstudio.cafe.core.network.ApiCaller
import id.kongstudio.cafe.core.network.ApiConfig
import id.kongstudio.cafe.feature.auth.session.LoginSession
import id.kongstudio.cafe.feature.dayplan.DayPlanLink
import id.kongstudio.cafe.feature.dayplan.DayPlanViewModel
import id.kongstudio.cafe.feature.dayplan.KtorDayPlanRepository
import id.kongstudio.cafe.feature.leave.LeaveRoute
import id.kongstudio.cafe.feature.overtime.OvertimeRoute
import io.ktor.client.HttpClient

@Composable
internal fun LeaveOvertimeRoute(
    session: LoginSession,
    client: HttpClient,
    onSessionExpired: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val api = remember(session.accessToken) { ApiCaller(client, ApiConfig.V2_BASE_URL, session.accessToken) }
    val dayPlanViewModel = viewModel(key = "day-plan-${session.accessToken}") {
        DayPlanViewModel(repository = KtorDayPlanRepository(api), onSessionExpired = onSessionExpired)
    }
    val dayPlan by dayPlanViewModel.state.collectAsState()
    var selectedIndex by rememberSaveable { mutableIntStateOf(0) }

    LifecycleResumeEffect(dayPlanViewModel) {
        dayPlanViewModel.load()
        onPauseOrDispose {}
    }

    LeaveOvertimePage(
        selectedIndex = selectedIndex,
        onSelect = { selectedIndex = it },
        leave = { LeaveRoute(session = session, client = client, onSessionExpired = onSessionExpired) },
        overtime = {
            OvertimeRoute(
                session = session,
                client = client,
                plan = DayPlanLink(dayPlan.plan?.scheduledOvertime, dayPlanViewModel::load),
                onSessionExpired = onSessionExpired,
            )
        },
        modifier = modifier,
    )
}
