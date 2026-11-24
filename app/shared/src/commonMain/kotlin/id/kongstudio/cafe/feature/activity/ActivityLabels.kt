package id.kongstudio.cafe.feature.activity

import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.vector.ImageVector
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.activity_auto_closed
import id.kongstudio.cafe.resources.activity_cash_closed
import id.kongstudio.cafe.resources.activity_cash_opened
import id.kongstudio.cafe.resources.activity_clock_in
import id.kongstudio.cafe.resources.activity_clock_out
import id.kongstudio.cafe.resources.activity_group_all
import id.kongstudio.cafe.resources.activity_group_attendance
import id.kongstudio.cafe.resources.activity_group_leave
import id.kongstudio.cafe.resources.activity_group_operations
import id.kongstudio.cafe.resources.activity_group_overtime
import id.kongstudio.cafe.resources.activity_group_task
import id.kongstudio.cafe.resources.activity_late
import id.kongstudio.cafe.resources.activity_leave_approved
import id.kongstudio.cafe.resources.activity_leave_decided
import id.kongstudio.cafe.resources.activity_leave_pending
import id.kongstudio.cafe.resources.activity_leave_permit
import id.kongstudio.cafe.resources.activity_leave_rejected
import id.kongstudio.cafe.resources.activity_leave_sick
import id.kongstudio.cafe.resources.activity_order_created
import id.kongstudio.cafe.resources.activity_order_voided
import id.kongstudio.cafe.resources.activity_overtime
import id.kongstudio.cafe.resources.activity_task_done
import id.kongstudio.cafe.resources.format_duration
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

private const val LATE_STATUS = "telat"
private const val AUTO_STATUS = "auto"
private const val SICK_TYPE = "sakit"
private const val APPROVED_STATUS = "disetujui"

@Composable
internal fun ActivityGroup.label(): String = stringResource(
    when (this) {
        ActivityGroup.All -> Res.string.activity_group_all
        ActivityGroup.Attendance -> Res.string.activity_group_attendance
        ActivityGroup.Task -> Res.string.activity_group_task
        ActivityGroup.Overtime -> Res.string.activity_group_overtime
        ActivityGroup.Leave -> Res.string.activity_group_leave
        ActivityGroup.Operations -> Res.string.activity_group_operations
    },
)

@Composable
internal fun ActivityEvent.title(): String = stringResource(
    when (action) {
        ActivityAction.ClockIn -> Res.string.activity_clock_in
        ActivityAction.ClockOut -> Res.string.activity_clock_out
        ActivityAction.TaskDone -> Res.string.activity_task_done
        ActivityAction.OvertimeRecorded -> Res.string.activity_overtime
        ActivityAction.LeaveRequested ->
            if (subject == SICK_TYPE) Res.string.activity_leave_sick else Res.string.activity_leave_permit
        ActivityAction.LeaveDecided -> Res.string.activity_leave_decided
        ActivityAction.OrderCreated -> Res.string.activity_order_created
        ActivityAction.OrderVoided -> Res.string.activity_order_voided
        ActivityAction.CashOpened -> Res.string.activity_cash_opened
        ActivityAction.CashClosed -> Res.string.activity_cash_closed
    },
)

@Composable
internal fun ActivityEvent.detail(): String? = when (action) {
    ActivityAction.ClockIn -> if (status == LATE_STATUS) stringResource(Res.string.activity_late) else null
    ActivityAction.ClockOut -> if (status == AUTO_STATUS) stringResource(Res.string.activity_auto_closed) else null
    ActivityAction.OvertimeRecorded -> minutes?.let {
        val (hours, rest) = DateTimeFormat.durationParts(it)
        stringResource(Res.string.format_duration, hours, rest)
    }
    ActivityAction.LeaveRequested -> stringResource(Res.string.activity_leave_pending)
    ActivityAction.LeaveDecided -> stringResource(
        if (status == APPROVED_STATUS) Res.string.activity_leave_approved else Res.string.activity_leave_rejected,
    )
    ActivityAction.TaskDone,
    ActivityAction.OrderCreated,
    ActivityAction.OrderVoided,
    ActivityAction.CashOpened,
    ActivityAction.CashClosed,
    -> subject
}

internal val ActivityEvent.icon: ImageVector
    get() = when (action) {
        ActivityAction.ClockIn, ActivityAction.ClockOut -> AppIcons.CalendarCheck
        ActivityAction.TaskDone -> AppIcons.Checklist
        ActivityAction.OvertimeRecorded -> AppIcons.Moon
        ActivityAction.LeaveRequested, ActivityAction.LeaveDecided -> AppIcons.Briefcase
        ActivityAction.OrderCreated, ActivityAction.OrderVoided -> AppIcons.Cart
        ActivityAction.CashOpened, ActivityAction.CashClosed -> AppIcons.Cash
    }
