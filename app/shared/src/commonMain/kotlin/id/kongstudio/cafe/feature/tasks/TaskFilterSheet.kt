package id.kongstudio.cafe.feature.tasks

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.tasks_filter_count
import id.kongstudio.cafe.resources.tasks_filter_date
import id.kongstudio.cafe.resources.tasks_filter_from
import id.kongstudio.cafe.resources.tasks_filter_hint
import id.kongstudio.cafe.resources.tasks_filter_no_match
import id.kongstudio.cafe.resources.tasks_filter_outlet
import id.kongstudio.cafe.resources.tasks_filter_outlet_all
import id.kongstudio.cafe.resources.tasks_filter_period_custom
import id.kongstudio.cafe.resources.tasks_filter_period_month
import id.kongstudio.cafe.resources.tasks_filter_period_today
import id.kongstudio.cafe.resources.tasks_filter_period_week
import id.kongstudio.cafe.resources.tasks_filter_person
import id.kongstudio.cafe.resources.tasks_filter_person_all
import id.kongstudio.cafe.resources.tasks_filter_person_mine
import id.kongstudio.cafe.resources.tasks_filter_person_search
import id.kongstudio.cafe.resources.tasks_filter_reset
import id.kongstudio.cafe.resources.tasks_filter_title
import id.kongstudio.cafe.resources.tasks_filter_to
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.choiceflow.ChoiceFlow
import id.kongstudio.cafe.ui.component.daterangefields.DateRangeFields
import id.kongstudio.cafe.ui.component.dropdownfield.DropdownField
import id.kongstudio.cafe.ui.component.dropdownfield.DropdownOption
import id.kongstudio.cafe.ui.component.iconbutton.AppIconButton
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

/** Lembar penyaring tugas (tanggal, orang, cabang) yang langsung berlaku tanpa tombol terapkan, dengan ikon di pojok bawah untuk kembali ke bawaan. */
@Composable
internal fun TaskFilterSheet(
    state: TaskUiState,
    ownUserId: String,
    actions: TaskActions,
    onDismiss: () -> Unit,
) {
    val colors = AppTheme.colors
    val periods = TaskPeriod.entries
    val outlets = state.options?.outlets.orEmpty()
    val everyone = stringResource(Res.string.tasks_filter_person_all)
    val mine = stringResource(Res.string.tasks_filter_person_mine)
    val allOutlets = stringResource(Res.string.tasks_filter_outlet_all)
    val people = buildList {
        add(DropdownOption(key = null, label = everyone))
        add(DropdownOption(key = ownUserId, label = mine))
        state.options?.assignees.orEmpty()
            .filter { it.id != ownUserId }
            .forEach { add(DropdownOption(key = it.id, label = it.name)) }
    }

    AppBottomSheet(title = stringResource(Res.string.tasks_filter_title), onDismiss = onDismiss) {
        Column(verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md)) {
            AppText(
                text = stringResource(Res.string.tasks_filter_count, state.total.toString()),
                role = TextRole.Caption,
                color = colors.contentMuted,
            )
            ChoiceFlow(
                label = stringResource(Res.string.tasks_filter_date),
                options = periods.map { periodLabel(it) },
                selectedIndex = periods.indexOf(state.period),
                onSelect = { actions.onPeriodChange(periods[it]) },
            )
            if (state.period == TaskPeriod.Custom) {
                DateRangeFields(
                    from = state.customFrom,
                    to = state.customTo,
                    today = DateTimeFormat.todayWib(),
                    fromLabel = stringResource(Res.string.tasks_filter_from),
                    toLabel = stringResource(Res.string.tasks_filter_to),
                    onChange = actions.onCustomRangeChange,
                    sideBySide = true,
                )
            }
            DropdownField(
                label = stringResource(Res.string.tasks_filter_person),
                options = people,
                selectedKey = state.assigneeId,
                onSelect = actions.onAssigneeChange,
                searchLabel = stringResource(Res.string.tasks_filter_person_search),
                emptyText = stringResource(Res.string.tasks_filter_no_match),
            )
            DropdownField(
                label = stringResource(Res.string.tasks_filter_outlet),
                options = listOf(DropdownOption(key = null, label = allOutlets)) +
                    outlets.map { DropdownOption(key = it.id, label = it.name) },
                selectedKey = state.outletId,
                onSelect = actions.onOutletChange,
            )
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.md),
            ) {
                AppText(
                    text = stringResource(Res.string.tasks_filter_hint),
                    role = TextRole.Caption,
                    color = colors.contentMuted,
                    modifier = Modifier.weight(1f),
                )
                AppIconButton(
                    icon = AppIcons.Refresh,
                    contentDescription = stringResource(Res.string.tasks_filter_reset),
                    onClick = actions.onResetFilters,
                    tint = colors.primary,
                    containerColor = colors.selected,
                )
            }
        }
    }
}

@Composable
private fun periodLabel(period: TaskPeriod): String = stringResource(
    when (period) {
        TaskPeriod.ThisMonth -> Res.string.tasks_filter_period_month
        TaskPeriod.Today -> Res.string.tasks_filter_period_today
        TaskPeriod.Week -> Res.string.tasks_filter_period_week
        TaskPeriod.Custom -> Res.string.tasks_filter_period_custom
    },
)
