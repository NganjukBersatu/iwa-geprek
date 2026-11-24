package id.kongstudio.cafe.feature.tasks

import id.kongstudio.cafe.feature.batches.BatchAnswer
import id.kongstudio.cafe.ui.component.mediafield.PickedMedia

/** Semua yang bisa dilakukan layar tugas, dikumpulkan agar halaman tidak membawa belasan parameter. */
internal class TaskActions(
    val onFilterChange: (TaskFilter) -> Unit,
    val onPeriodChange: (TaskPeriod) -> Unit,
    val onCustomRangeChange: (from: String, to: String) -> Unit,
    val onSearchChange: (String) -> Unit,
    val onAssigneeChange: (String?) -> Unit,
    val onResetFilters: () -> Unit,
    val onOutletChange: (String?) -> Unit,
    val onPageChange: (Int) -> Unit,
    val onRetry: () -> Unit,
    val onLoadOptions: (outletId: String?) -> Unit,
    val onCreate: (task: NewTask, onSuccess: () -> Unit) -> Unit,
    val onUpdate: (
        taskId: String,
        title: String,
        description: String,
        due: String?,
        onSuccess: () -> Unit,
    ) -> Unit,
    val onComplete: (taskId: String, note: String, media: List<PickedMedia>, onSuccess: () -> Unit) -> Unit,
    val onAddAttachments: (taskId: String, media: List<PickedMedia>, onSuccess: () -> Unit) -> Unit,
    val onRemoveAttachment: (taskId: String, attachmentId: String) -> Unit,
    val onDelete: (taskId: String, onSuccess: () -> Unit) -> Unit,
    val onClearSubmitError: () -> Unit,
    val onCompleteBatch: (batchId: String, answers: List<BatchAnswer>, onSuccess: () -> Unit) -> Unit,
    val onClearBatchError: () -> Unit,
    val onOpenFix: (runId: String) -> Unit,
    val onCloseFix: () -> Unit,
    val onFixBatch: (runId: String, answers: List<BatchAnswer>, onSuccess: () -> Unit) -> Unit,
    val onCancelBatch: (runId: String, onSuccess: () -> Unit) -> Unit,
    val onDeleteBatch: (runId: String, onSuccess: () -> Unit) -> Unit,
    val onFixCompletion: (taskId: String, note: String, onSuccess: () -> Unit) -> Unit,
    val onOpenSourceRun: (taskId: String) -> Unit,
    val onCloseSourceRun: () -> Unit,
)
