package id.kongstudio.cafe.feature.dashboard

import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.feature.batches.Batch
import id.kongstudio.cafe.feature.batches.BatchKind

internal object DashboardMapper {
    fun pendingTasks(tasks: List<TaskDto>): List<PendingTask> =
        tasks
            .filter { it.status == "belum" }
            .map { task ->
                PendingTask(
                    title = task.title,
                    due = DateTimeFormat.stamp(task.dueAt),
                    kind = PendingKind.Personal,
                )
            }

    /** Tugas rutin dan tugas outlet yang belum diisi masuk daftar tugas tertunda. */
    fun pendingBatches(batches: List<Batch>): List<PendingTask> =
        batches
            .filter { !it.completed }
            .map { batch -> PendingTask(title = batch.name, due = null, kind = if (batch.kind == BatchKind.Routine) PendingKind.Routine else PendingKind.Outlet, caption = batch.rangeLabel) }
}
