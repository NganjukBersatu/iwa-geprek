package id.kongstudio.cafe.feature.tasks

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.format.whenLabel
import id.kongstudio.cafe.core.text.resolve
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.feature.batches.Batch
import id.kongstudio.cafe.feature.batches.BatchFormSheet
import id.kongstudio.cafe.feature.batches.BatchManageSheet
import id.kongstudio.cafe.feature.batches.BatchKind
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.batch_routine_done
import id.kongstudio.cafe.resources.batch_routine_tag
import id.kongstudio.cafe.resources.batch_done
import id.kongstudio.cafe.resources.batch_each_done
import id.kongstudio.cafe.resources.batch_fill
import id.kongstudio.cafe.resources.batch_fill_each
import id.kongstudio.cafe.resources.batch_fill_one
import id.kongstudio.cafe.resources.batch_tag
import id.kongstudio.cafe.resources.dashboard_task_due
import id.kongstudio.cafe.resources.schedule_mine
import id.kongstudio.cafe.resources.tasks_complete_submit
import id.kongstudio.cafe.resources.tasks_add_short
import id.kongstudio.cafe.resources.batch_fix_submit
import id.kongstudio.cafe.resources.batch_manage_action
import id.kongstudio.cafe.resources.tasks_empty
import id.kongstudio.cafe.resources.tasks_filter_done
import id.kongstudio.cafe.resources.tasks_filter_open
import id.kongstudio.cafe.resources.tasks_filter_pending
import id.kongstudio.cafe.resources.tasks_search_label
import id.kongstudio.cafe.resources.tasks_section_personal
import id.kongstudio.cafe.ui.component.batchcard.BatchCard
import id.kongstudio.cafe.ui.component.sectiontitle.SectionTitle
import id.kongstudio.cafe.ui.component.taskcard.TaskCard
import id.kongstudio.cafe.ui.component.taskcard.TaskCardTone
import id.kongstudio.cafe.ui.component.failurestate.FailureState
import id.kongstudio.cafe.ui.component.floatingpillbutton.FloatingPillButton
import id.kongstudio.cafe.ui.component.iconbutton.AppIconButton
import id.kongstudio.cafe.ui.component.loadingstate.LoadingState
import id.kongstudio.cafe.ui.component.pagination.Pagination
import id.kongstudio.cafe.ui.component.statelistcard.StateListCard
import id.kongstudio.cafe.ui.component.searchfield.SearchField
import id.kongstudio.cafe.ui.component.segmentedcontrol.SegmentedControl
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

@Composable
internal fun TaskScreen(
    state: TaskUiState,
    ownUserId: String,
    actions: TaskActions,
    modifier: Modifier = Modifier,
) {
    val spacing = AppTheme.spacing
    val colors = AppTheme.colors
    var selectedId by remember { mutableStateOf<String?>(null) }
    var creating by remember { mutableStateOf(false) }
    var editing by remember { mutableStateOf(false) }
    var filtering by remember { mutableStateOf(false) }
    var fillingBatchId by remember { mutableStateOf<String?>(null) }
    var managingBatchId by remember { mutableStateOf<String?>(null) }
    val selected = state.items.firstOrNull { it.id == selectedId }

    state.batches.firstOrNull { it.id == fillingBatchId }?.let { batch ->
        BatchFormSheet(
            batch = batch,
            submitting = state.batchSubmitting,
            error = state.batchError?.resolve(),
            onSubmit = { answers -> actions.onCompleteBatch(batch.id, answers) { fillingBatchId = null } },
            onDismiss = {
                actions.onClearBatchError()
                fillingBatchId = null
            },
        )
    }

    val fixing = state.fixing
    if (fixing != null) {
        BatchFormSheet(
            batch = fixing.batch,
            submitting = state.batchSubmitting,
            error = state.batchError?.resolve(),
            onSubmit = { answers -> actions.onFixBatch(fixing.runId, answers) { managingBatchId = null } },
            onDismiss = actions.onCloseFix,
            initialValues = fixing.values,
            keptPhotoUrls = fixing.photoUrls,
            submitLabel = stringResource(Res.string.batch_fix_submit),
        )
    } else {
        state.batches.firstOrNull { it.id == managingBatchId && it.manageable }?.let { batch ->
            val runId = batch.runId.orEmpty()
            BatchManageSheet(
                batch = batch,
                submitting = state.batchSubmitting,
                error = state.batchError?.resolve(),
                onFix = { actions.onOpenFix(runId) },
                onCancel = { actions.onCancelBatch(runId) { managingBatchId = null } },
                onDelete = { actions.onDeleteBatch(runId) { managingBatchId = null } },
                onDismiss = {
                    actions.onClearBatchError()
                    managingBatchId = null
                },
            )
        }
    }

    if (filtering) {
        TaskFilterSheet(state = state, ownUserId = ownUserId, actions = actions, onDismiss = { filtering = false })
    }

    if (creating) {
        TaskFormSheet(
            options = state.options,
            submitting = state.submitting,
            error = state.submitError,
            onSubmit = { task -> actions.onCreate(task) { creating = false } },
            onLoadOptions = actions.onLoadOptions,
            onDismiss = {
                actions.onClearSubmitError()
                creating = false
            },
        )
    }

    state.sourceTaskId?.let { taskId ->
        SourceRunSheet(
            run = state.sourceRun,
            failure = state.sourceFailure,
            onRetry = { actions.onOpenSourceRun(taskId) },
            onDismiss = actions.onCloseSourceRun,
        )
    }

    selected?.let { task ->
        TaskDetailSheet(
            task = task,
            submitting = state.submitting,
            submitError = state.submitError,
            onComplete = { note, media -> actions.onComplete(task.id, note, media) { selectedId = null } },
            onAddAttachments = { media -> actions.onAddAttachments(task.id, media) {} },
            onRemoveAttachment = { attachment -> actions.onRemoveAttachment(task.id, attachment.id) },
            onEdit = { editing = true },
            onFixNote = { note -> actions.onFixCompletion(task.id, note) {} },
            onOpenSource = { actions.onOpenSourceRun(task.id) },
            onDelete = { actions.onDelete(task.id) { selectedId = null } },
            onDismiss = {
                actions.onClearSubmitError()
                selectedId = null
            },
        )

        if (editing) {
            TaskEditSheet(
                task = task,
                submitting = state.submitting,
                error = state.submitError,
                onSubmit = { title, description, due ->
                    actions.onUpdate(task.id, title, description, due?.toIso()) { editing = false }
                },
                onDismiss = {
                    actions.onClearSubmitError()
                    editing = false
                },
            )
        }
    }

    Box(modifier = modifier.fillMaxSize(), contentAlignment = Alignment.TopCenter) {
        Box(modifier = Modifier.widthIn(max = AppTheme.sizes.contentMaxWidth).fillMaxHeight()) {
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(
                    horizontal = AppTheme.windowSize.pagePadding,
                    vertical = spacing.lg,
                ),
                verticalArrangement = Arrangement.spacedBy(spacing.md),
            ) {
                item {
                    Row(
                        verticalAlignment = Alignment.Bottom,
                        horizontalArrangement = Arrangement.spacedBy(spacing.sm),
                    ) {
                        SearchField(
                            value = state.search,
                            onValueChange = actions.onSearchChange,
                            label = stringResource(Res.string.tasks_search_label),
                            modifier = Modifier.weight(1f),
                        )
                        AppIconButton(
                            icon = AppIcons.Adjustments,
                            contentDescription = stringResource(Res.string.tasks_filter_open),
                            onClick = { filtering = true },
                            tint = colors.onPrimary,
                            badge = state.activeFilterCount.takeIf { it > 0 }?.toString(),
                            containerColor = colors.primary,
                            badgeColor = colors.accent,
                            onBadgeColor = colors.content,
                        )
                    }
                }

                item {
                    SegmentedControl(
                        options = listOf(
                            stringResource(Res.string.tasks_filter_pending),
                            stringResource(Res.string.tasks_filter_done),
                        ),
                        selectedIndex = TaskFilter.entries.indexOf(state.filter),
                        onSelect = { actions.onFilterChange(TaskFilter.entries[it]) },
                    )
                }

                // Tugas rutin dan tugas outlet mengikuti tab yang sama dengan tugas karyawan, masing-masing di bagian berjudul.
                val showDone = state.filter == TaskFilter.Done
                val matching = matchingBatches(state, ownUserId)
                BatchKind.entries.forEach { kind ->
                    val shown = matching.filter { it.kind == kind && it.completed == showDone }
                    if (shown.isNotEmpty()) {
                        val routine = kind == BatchKind.Routine
                        item(key = "section-${kind.apiValue}") {
                            SectionTitle(text = stringResource(if (routine) Res.string.batch_routine_tag else Res.string.batch_tag), padded = false)
                        }
                        items(shown, key = { it.id }) { batch ->
                            BatchCard(
                                title = batch.name,
                                rangeLabel = batch.rangeLabel,
                                completed = batch.completed,
                                tagLabel = stringResource(if (routine) Res.string.batch_routine_tag else Res.string.batch_tag),
                                fillLabel = stringResource(Res.string.batch_fill),
                                doneLabel = stringResource(
                                    when {
                                        !routine -> Res.string.batch_done
                                        batch.eachFills -> Res.string.batch_each_done
                                        else -> Res.string.batch_routine_done
                                    },
                                ),
                                onFill = { fillingBatchId = batch.id },
                                // Ikon dan keterangan pengisi membedakan tugas rutin dari tugas outlet tanpa membaca lencananya.
                                icon = if (routine) AppIcons.CalendarCheck else AppIcons.UsersGroup,
                                note = stringResource(if (batch.eachFills) Res.string.batch_fill_each else Res.string.batch_fill_one).takeIf { routine },
                                // Tugas rutin warna teks dan tugas outlet warna utama, dua warna palet yang senada tetapi tidak tertukar sekilas.
                                tone = if (routine) TaskCardTone.Green else TaskCardTone.Tan,
                                onManage = { managingBatchId = batch.id }.takeIf { batch.manageable },
                                manageLabel = stringResource(Res.string.batch_manage_action),
                            )
                        }
                    }
                }

                item(key = "section-personal") { SectionTitle(text = stringResource(Res.string.tasks_section_personal), padded = false) }

                when {
                    state.loading -> item { LoadingState() }

                    state.failure != null -> item { FailureState(failure = state.failure!!, onRetry = actions.onRetry) }

                    state.items.isEmpty() -> item { StateListCard(loading = false, empty = true, emptyText = stringResource(Res.string.tasks_empty)) {} }

                    else -> {
                        items(state.items, key = { it.id }) { task ->
                            val open = { selectedId = task.id }
                            TaskCard(
                                title = task.title,
                                tone = TaskCardTone.Light,
                                icon = AppIcons.Checklist,
                                completed = task.done,
                                caption = taskCaption(task),
                                // Tanda sama dengan baris milik sendiri di Jadwal, supaya tugas sendiri terlihat di antara tugas cabang.
                                tagLabel = stringResource(Res.string.schedule_mine).takeIf { task.mine },
                                actionLabel = stringResource(Res.string.tasks_complete_submit).takeIf { task.canComplete },
                                onAction = open,
                                onClick = open,
                            )
                        }
                        if (state.pageCount > 1) {
                            item(key = "personal-pages") {
                                Pagination(page = state.page.coerceIn(0, state.pageCount - 1), pageCount = state.pageCount, onPageChange = actions.onPageChange)
                            }
                        }
                    }
                }

                item { Spacer(Modifier.height(spacing.touchTarget + spacing.lg)) }
            }

            FloatingPillButton(
                icon = AppIcons.Plus,
                label = stringResource(Res.string.tasks_add_short),
                onClick = { creating = true },
                modifier = Modifier
                    .align(Alignment.BottomEnd)
                    .padding(horizontal = AppTheme.windowSize.pagePadding, vertical = spacing.lg),
            )
        }
    }
}

private const val CaptionSeparator = " · "

/** Keterangan satu tugas karyawan: cabang, lalu waktu selesai atau batas waktunya. */
/** Tugas outlet dan tugas rutin hari ini yang lolos pencarian dan saringan yang sama dengan tugas karyawan. */
private fun matchingBatches(state: TaskUiState, ownUserId: String): List<Batch> {
    val today = DateTimeFormat.todayWib()
    val from = state.dateFrom
    val to = state.dateTo
    // Kartu ini hanya milik orang yang membuka dan hanya untuk hari ini, jadi saringan orang lain atau rentang tanpa hari ini menyembunyikannya.
    val forOther = state.assigneeId != null && state.assigneeId != ownUserId
    val outsideRange = (from != null && today < from) || (to != null && today > to)
    if (forOther || outsideRange) return emptyList()
    val word = state.search.trim()
    return if (word.isEmpty()) state.batches else state.batches.filter { it.name.contains(word, ignoreCase = true) }
}

@Composable
private fun taskCaption(task: TaskItem): String? {
    val timing = when {
        task.done -> task.doneAt?.let { whenLabel(it) }
        else -> task.due?.let { stringResource(Res.string.dashboard_task_due, whenLabel(it)) }
    }
    return listOfNotNull(task.outletName, timing).joinToString(CaptionSeparator).ifEmpty { null }
}
