package id.kongstudio.cafe.feature.dashboard

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import id.kongstudio.cafe.core.format.durationLabel
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.core.format.whenLabel
import id.kongstudio.cafe.core.text.resolve
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.common_loading
import id.kongstudio.cafe.resources.dashboard_empty_tasks
import id.kongstudio.cafe.resources.dashboard_hero_empty
import id.kongstudio.cafe.resources.dashboard_hero_label
import id.kongstudio.cafe.resources.dashboard_hero_sub
import id.kongstudio.cafe.resources.dashboard_hero_value
import id.kongstudio.cafe.resources.dashboard_open_attendance
import id.kongstudio.cafe.resources.dashboard_section_attendance
import id.kongstudio.cafe.resources.dashboard_stat_overtime
import id.kongstudio.cafe.resources.dashboard_stat_penalty
import id.kongstudio.cafe.resources.dashboard_stat_work
import id.kongstudio.cafe.resources.dashboard_open_tasks
import id.kongstudio.cafe.resources.dashboard_task_count
import id.kongstudio.cafe.resources.dashboard_task_due
import id.kongstudio.cafe.resources.dashboard_task_routine
import id.kongstudio.cafe.resources.dashboard_task_kind_routine
import id.kongstudio.cafe.resources.dashboard_task_kind_outlet
import id.kongstudio.cafe.resources.dashboard_task_kind_personal
import id.kongstudio.cafe.resources.dashboard_task_label
import id.kongstudio.cafe.resources.dashboard_task_outlet
import id.kongstudio.cafe.resources.dashboard_task_personal
import id.kongstudio.cafe.resources.months
import id.kongstudio.cafe.resources.sheet_close
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.bannerbackdrop.BannerBackdrop
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.centeredstat.CenteredStat
import id.kongstudio.cafe.ui.component.iconpill.IconPill
import id.kongstudio.cafe.ui.component.divideditems.DividedItems
import id.kongstudio.cafe.ui.component.expandablecard.ExpandableCardHost
import id.kongstudio.cafe.ui.component.expandablecard.ExpandableCardSpec
import id.kongstudio.cafe.ui.component.failurestate.FailureState
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.progressring.ProgressRing
import id.kongstudio.cafe.ui.component.scaletoheight.ScaleToHeight
import id.kongstudio.cafe.ui.component.scaletoheight.ScaledDensity
import id.kongstudio.cafe.ui.component.scaletoheight.scaleForHeight
import androidx.compose.foundation.layout.BoxWithConstraints
import id.kongstudio.cafe.ui.component.statcard.StatCard
import id.kongstudio.cafe.ui.component.statelistcard.StateListCard
import id.kongstudio.cafe.ui.component.usercard.UserCard
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import kotlin.math.roundToInt
import org.jetbrains.compose.resources.stringArrayResource
import org.jetbrains.compose.resources.stringResource

private const val TaskSkeletonRows = 2
private const val PercentFull = 100
private const val HeroKey = "attendance"
private const val TaskKey = "tasks"

@Composable
internal fun DashboardScreen(
    state: DashboardUiState,
    headerName: String,
    headerSubtitle: String,
    headerPhotoUrl: String?,
    onRetry: () -> Unit,
    onOpenAttendance: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val spacing = AppTheme.spacing
    val colors = AppTheme.colors
    // Tinggi alami tiap blok jadi bobot sekaligus acuan skala, jadi semua blok membesar atau mengecil bersama.
    val bannerBaseline = AppTheme.sizes.bannerBaseline
    val tileBaseline = AppTheme.sizes.tileBaseline
    val contentBaseline = tileBaseline * 3 + spacing.md * 2 + spacing.lg
    val failure = state.failure
    val attendance = state.attendance
    val months = stringArrayResource(Res.array.months)
    var openKey by remember { mutableStateOf<String?>(null) }

    val total = attendance?.let { it.present + it.notPresent } ?: 0
    val progress = if (attendance != null && total > 0) attendance.present.toFloat() / total else 0f
    val heroLabel = attendance?.let {
        stringResource(Res.string.dashboard_hero_label, months[it.month.month - 1], it.month.year.toString())
    } ?: stringResource(Res.string.dashboard_section_attendance)
    val heroValue = if (attendance == null) {
        stringResource(Res.string.dashboard_hero_empty)
    } else {
        stringResource(Res.string.dashboard_hero_value, attendance.present.toString(), total.toString())
    }
    val heroSub = if (attendance == null) {
        stringResource(Res.string.common_loading)
    } else {
        stringResource(Res.string.dashboard_hero_sub, attendance.late.toString(), attendance.notPresent.toString())
    }
    val taskValue = if (state.loading) {
        stringResource(Res.string.dashboard_hero_empty)
    } else {
        stringResource(Res.string.dashboard_task_count, state.pendingTasks.size.toString())
    }
    val personalCount = state.pendingTasks.count { it.kind == PendingKind.Personal }
    val routineCount = state.pendingTasks.count { it.kind == PendingKind.Routine }
    val outletCount = state.pendingTasks.count { it.kind == PendingKind.Outlet }

    val hero = ExpandableCardSpec(
        key = HeroKey,
        containerColor = Color.Transparent,
        contentPadding = PaddingValues(vertical = spacing.lg),
        actionColor = colors.onPrimarySubtle,
        actionTint = colors.onPrimary,
        openLabel = stringResource(Res.string.dashboard_open_attendance),
        closeLabel = stringResource(Res.string.sheet_close),
        leading = {
            ProgressRing(
                progress = progress,
                label = "${(progress * PercentFull).roundToInt()}%",
                trackColor = colors.onPrimarySubtle,
                indicatorColor = colors.accent,
                labelColor = colors.onPrimary,
            )
        },
        head = {
            AppText(text = heroLabel, role = TextRole.Caption, color = colors.onPrimaryMuted)
            AppText(text = heroValue, role = TextRole.Title, color = colors.onPrimary)
            AppText(text = heroSub, role = TextRole.Caption, color = colors.onPrimaryMuted)
        },
        body = {},
    )
    val tasks = ExpandableCardSpec(
        key = TaskKey,
        containerColor = colors.surface,
        // Jarak tepi sama dengan ubin angka di atasnya, karena tinggi kartu ini sama dan jarak bawaan memotong angkanya.
        contentPadding = PaddingValues(spacing.md),
        actionColor = colors.selected,
        actionTint = colors.primary,
        centered = true,
        openLabel = stringResource(Res.string.dashboard_open_tasks),
        closeLabel = stringResource(Res.string.sheet_close),
        head = {
            CenteredStat(
                label = stringResource(Res.string.dashboard_task_label),
                value = taskValue,
                icon = AppIcons.Checklist,
                caption = if (!state.loading && state.pendingTasks.isEmpty()) stringResource(Res.string.dashboard_empty_tasks) else null,
            )
        },
        body = {
            if (!state.loading && state.pendingTasks.isNotEmpty()) {
                // Hanya di isi kartu yang terbuka, karena di kartu tertutup pil ini membuat angkanya terpotong; FlowRow membuat kartu beranimasi ini crash, jadi barisnya ditetapkan dua.
                Column(
                    modifier = Modifier.align(Alignment.CenterHorizontally).padding(bottom = spacing.md),
                    verticalArrangement = Arrangement.spacedBy(spacing.sm),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    Row(horizontalArrangement = Arrangement.spacedBy(spacing.sm)) {
                        IconPill(
                            icon = AppIcons.User,
                            text = stringResource(Res.string.dashboard_task_personal, personalCount.toString()),
                        )
                        IconPill(
                            icon = AppIcons.CalendarCheck,
                            text = stringResource(Res.string.dashboard_task_routine, routineCount.toString()),
                            containerColor = colors.primary,
                            contentColor = colors.onPrimary,
                        )
                    }
                    IconPill(
                        icon = AppIcons.UsersGroup,
                        text = stringResource(Res.string.dashboard_task_outlet, outletCount.toString()),
                        containerColor = colors.accent,
                    )
                }
            }
            StateListCard(
                loading = state.loading,
                empty = state.pendingTasks.isEmpty(),
                emptyText = stringResource(Res.string.dashboard_empty_tasks),
                skeletonRows = TaskSkeletonRows,
            ) {
                DividedItems(state.pendingTasks) { task ->
                    ListRow(
                        title = task.title,
                        caption = task.caption ?: task.due?.let { stringResource(Res.string.dashboard_task_due, whenLabel(it)) },
                        trailing = {
                            StatusBadge(
                                text = stringResource(
                                    when (task.kind) {
                                        PendingKind.Personal -> Res.string.dashboard_task_kind_personal
                                        PendingKind.Routine -> Res.string.dashboard_task_kind_routine
                                        PendingKind.Outlet -> Res.string.dashboard_task_kind_outlet
                                    },
                                ),
                                tone = when (task.kind) {
                                    PendingKind.Personal -> BadgeTone.Positive
                                    PendingKind.Routine -> BadgeTone.Strong
                                    PendingKind.Outlet -> BadgeTone.Accent
                                },
                            )
                        },
                    )
                }
            }
        },
    )

    ExpandableCardHost(
        expanded = if (openKey == tasks.key) tasks else null,
        onOpen = { if (it.key == HeroKey) onOpenAttendance() else openKey = it.key },
        onClose = { openKey = null },
        modifier = modifier.fillMaxSize(),
    ) {
        // Skala mengikuti tinggi layar, tetapi tinggi banner mengikuti isinya supaya teks tidak terpotong; ubin mengisi sisanya.
        BoxWithConstraints(modifier = Modifier.fillMaxSize()) {
        val bannerScale = scaleForHeight(maxHeight, bannerBaseline + contentBaseline)
        Column(modifier = Modifier.fillMaxSize(), horizontalAlignment = Alignment.CenterHorizontally) {
            ScaledDensity(scale = bannerScale) {
                BannerBackdrop(modifier = Modifier.fillMaxWidth()) {
                    Column(
                        modifier = Modifier
                            .widthIn(max = AppTheme.sizes.contentMaxWidth)
                            .fillMaxWidth()
                            .padding(horizontal = AppTheme.windowSize.pagePadding),
                        verticalArrangement = Arrangement.spacedBy(spacing.sm),
                    ) {
                        UserCard(
                            name = headerName,
                            subtitle = headerSubtitle,
                            photoUrl = headerPhotoUrl,
                            tag = state.todayAssignment?.resolve(),
                            containerColor = Color.Transparent,
                            contentPadding = PaddingValues(vertical = spacing.lg),
                        )
                        if (failure == null) ExpandableCard(hero, Modifier.fillMaxWidth())
                    }
                }
            }
            Column(
                modifier = Modifier
                    .weight(1f)
                    .widthIn(max = AppTheme.sizes.contentMaxWidth)
                    .fillMaxWidth()
                    .padding(start = AppTheme.windowSize.pagePadding, end = AppTheme.windowSize.pagePadding, bottom = spacing.lg),
                verticalArrangement = Arrangement.spacedBy(spacing.md),
            ) {
                if (failure != null) {
                    ListCard { FailureState(failure = failure, onRetry = onRetry) }
                } else {
                    if (attendance != null) AttendanceTiles(attendance)
                    ScaleToHeight(baseline = tileBaseline, modifier = Modifier.weight(tileBaseline.value)) {
                        ExpandableCard(tasks, Modifier.fillMaxSize())
                    }
                }
            }
        }
        }
    }
}

/** Jam kerja, lembur, dan potongan bulan ini; ringkasan yang tetap terlihat di dasbor. */
@Composable
private fun ColumnScope.AttendanceTiles(attendance: AttendanceMonth) {
    val spacing = AppTheme.spacing
    val colors = AppTheme.colors
    val tileBaseline = AppTheme.sizes.tileBaseline
    // Lebar alami ubin angka membatasi skala agar label dan nilainya tidak terpotong.
    val tileBaselineWidth = AppTheme.sizes.cardMinWidth

    Row(
        modifier = Modifier.weight(tileBaseline.value),
        horizontalArrangement = Arrangement.spacedBy(spacing.sm),
    ) {
        ScaleToHeight(baseline = tileBaseline, baselineWidth = tileBaselineWidth, modifier = Modifier.weight(1f).fillMaxHeight()) {
            StatCard(
                label = stringResource(Res.string.dashboard_stat_work),
                value = durationLabel(attendance.workMinutes),
                modifier = Modifier.fillMaxSize(),
                icon = AppIcons.Clock,
                centered = true,
            )
        }
        ScaleToHeight(baseline = tileBaseline, baselineWidth = tileBaselineWidth, modifier = Modifier.weight(1f).fillMaxHeight()) {
            StatCard(
                label = stringResource(Res.string.dashboard_stat_overtime),
                value = durationLabel(attendance.overtimeMinutes),
                modifier = Modifier.fillMaxSize(),
                icon = AppIcons.History,
                centered = true,
            )
        }
    }
    ScaleToHeight(baseline = tileBaseline, baselineWidth = tileBaselineWidth, modifier = Modifier.weight(tileBaseline.value)) {
        StatCard(
            label = stringResource(Res.string.dashboard_stat_penalty),
            value = formatRupiah(attendance.penalty),
            modifier = Modifier.fillMaxSize(),
            valueColor = if (attendance.penalty > 0) colors.danger else colors.content,
            icon = AppIcons.Alert,
            centered = true,
        )
    }
}
