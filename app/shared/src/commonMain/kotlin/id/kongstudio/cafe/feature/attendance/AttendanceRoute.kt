package id.kongstudio.cafe.feature.attendance

import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.lifecycle.compose.LifecycleResumeEffect
import androidx.lifecycle.viewmodel.compose.viewModel
import id.kongstudio.cafe.core.network.ApiCaller
import id.kongstudio.cafe.core.network.ApiConfig
import id.kongstudio.cafe.feature.attendance.selfschedule.KtorSelfScheduleRepository
import id.kongstudio.cafe.feature.attendance.selfschedule.SelfScheduleSheets
import id.kongstudio.cafe.feature.attendance.selfschedule.SelfScheduleViewModel
import id.kongstudio.cafe.feature.auth.session.LoginSession
import id.kongstudio.cafe.feature.dayplan.DayPlanViewModel
import id.kongstudio.cafe.feature.dayplan.KtorDayPlanRepository
import id.kongstudio.cafe.feature.location.DeviceLocation
import io.ktor.client.HttpClient

@Composable
internal fun AttendanceRoute(
    session: LoginSession,
    client: HttpClient,
    location: DeviceLocation,
    onSessionExpired: () -> Unit,
    modifier: Modifier = Modifier,
    sections: @Composable ColumnScope.() -> Unit = {},
) {
    val api = remember(session.accessToken) { ApiCaller(client, ApiConfig.V2_BASE_URL, session.accessToken) }
    val viewModel = viewModel(key = "attendance-${session.accessToken}") {
        AttendanceViewModel(
            repository = KtorAttendanceRepository(api),
            location = location,
            userName = session.user.name ?: session.user.username,
            onSessionExpired = onSessionExpired,
        )
    }
    val state by viewModel.state.collectAsState()
    val dayPlanViewModel = viewModel(key = "day-plan-${session.accessToken}") {
        DayPlanViewModel(repository = KtorDayPlanRepository(api), onSessionExpired = onSessionExpired)
    }
    val dayPlan by dayPlanViewModel.state.collectAsState()
    val selfScheduleViewModel = viewModel(key = "self-schedule-${session.accessToken}") {
        SelfScheduleViewModel(repository = KtorSelfScheduleRepository(api), onSessionExpired = onSessionExpired)
    }
    val selfSchedule by selfScheduleViewModel.state.collectAsState()

    LifecycleResumeEffect(viewModel) {
        viewModel.load()
        dayPlanViewModel.load()
        onPauseOrDispose {}
    }

    SelfScheduleSheets(
        state = selfSchedule,
        onContinue = selfScheduleViewModel::openForm,
        onSelectOutlet = selfScheduleViewModel::selectOutlet,
        onSelectRole = selfScheduleViewModel::selectRole,
        onSelectShift = selfScheduleViewModel::selectShift,
        onReasonChange = selfScheduleViewModel::changeReason,
        onSubmit = { selfScheduleViewModel.submit(viewModel::startSelfScheduled) },
        onDismiss = selfScheduleViewModel::close,
    )

    AttendanceScreen(
        state = state,
        onRetry = viewModel::load,
        onClock = viewModel::openSheet,
        onAcknowledge = viewModel::acknowledgeNotices,
        onSubmit = viewModel::submit,
        onDismissSheet = viewModel::closeSheet,
        onFinishCelebration = viewModel::finishCelebration,
        onSelfSchedule = selfScheduleViewModel::start,
        onRelocate = viewModel::locate,
        previewDistance = state.previewDistance(viewModel.location),
        plan = dayPlan.plan,
        modifier = modifier,
        sections = sections,
    )
}
