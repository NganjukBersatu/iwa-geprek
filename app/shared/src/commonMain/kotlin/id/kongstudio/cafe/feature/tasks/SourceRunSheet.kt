package id.kongstudio.cafe.feature.tasks

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.format.longDateLabel
import id.kongstudio.cafe.core.format.whenLabel
import id.kongstudio.cafe.core.text.UiText
import id.kongstudio.cafe.core.text.resolve
import id.kongstudio.cafe.feature.batches.BatchItemKind
import id.kongstudio.cafe.feature.batches.ToggleOk
import id.kongstudio.cafe.feature.batches.ToggleProblem
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.batch_toggle_ok
import id.kongstudio.cafe.resources.batch_toggle_problem
import id.kongstudio.cafe.resources.common_retry
import id.kongstudio.cafe.resources.tasks_detail_name
import id.kongstudio.cafe.resources.tasks_detail_outlet
import id.kongstudio.cafe.resources.tasks_source_day
import id.kongstudio.cafe.resources.tasks_source_done_at
import id.kongstudio.cafe.resources.tasks_source_empty_answer
import id.kongstudio.cafe.resources.tasks_source_filler
import id.kongstudio.cafe.resources.tasks_source_problems
import id.kongstudio.cafe.resources.tasks_source_title
import id.kongstudio.cafe.ui.component.attachmentgallery.AttachmentGallery
import id.kongstudio.cafe.ui.component.attachmentgallery.RemoteAttachment
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.detaillist.DetailList
import id.kongstudio.cafe.ui.component.detailrow.DetailRow
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.sectiontitle.SectionTitle
import id.kongstudio.cafe.ui.component.skeleton.SkeletonRows
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

private const val LoadingRows = 4

/** Isi pengisian yang ditindaklanjuti sebuah tugas: [run] kosong berarti masih dimuat, kecuali [failure] terisi. */
@Composable
internal fun SourceRunSheet(
    run: SourceRun?,
    failure: AppFailure?,
    onRetry: () -> Unit,
    onDismiss: () -> Unit,
) {
    AppBottomSheet(title = stringResource(Res.string.tasks_source_title), onDismiss = onDismiss) {
        Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md)) {
            when {
                failure != null -> {
                    InlineMessage(text = UiText.Failed(failure).resolve())
                    PrimaryButton(text = stringResource(Res.string.common_retry), onClick = onRetry)
                }

                run == null -> SkeletonRows(count = LoadingRows)

                else -> SourceRunContent(run)
            }
        }
    }
}

@Composable
private fun SourceRunContent(run: SourceRun) {
    val written = run.answers.filter { it.photoUrl == null }
    val photos = run.answers.filter { it.photoUrl != null }
    val rows = buildList<@Composable () -> Unit> {
        add { DetailRow(stringResource(Res.string.tasks_detail_name), value = run.batchName) }
        add { DetailRow(stringResource(Res.string.tasks_source_day), value = longDateLabel(run.day)) }
        add { DetailRow(stringResource(Res.string.tasks_detail_outlet), value = run.outletName) }
        run.completedBy?.let { name -> add { DetailRow(stringResource(Res.string.tasks_source_filler), value = name) } }
        run.completedAt?.let { at -> add { DetailRow(stringResource(Res.string.tasks_source_done_at), value = whenLabel(at)) } }
        written.forEach { answer -> add { AnswerRow(answer) } }
    }

    if (run.problems > 0) {
        StatusBadge(text = stringResource(Res.string.tasks_source_problems, run.problems), tone = BadgeTone.Danger)
    }
    DetailList(rows)
    photos.forEachIndexed { index, answer ->
        SectionTitle(answer.label)
        AttachmentGallery(
            attachments = listOf(RemoteAttachment(id = "source-$index", isVideo = false, url = answer.photoUrl.orEmpty(), removable = false)),
            onRemove = null,
        )
    }
}

@Composable
private fun AnswerRow(answer: SourceAnswer) {
    val isToggle = answer.kind == BatchItemKind.Toggle.apiValue
    when {
        isToggle && answer.value == ToggleProblem -> DetailRow(
            answer.label,
            valueContent = { StatusBadge(text = stringResource(Res.string.batch_toggle_problem), tone = BadgeTone.Danger) },
        )

        isToggle && answer.value == ToggleOk -> DetailRow(
            answer.label,
            valueContent = { StatusBadge(text = stringResource(Res.string.batch_toggle_ok), tone = BadgeTone.Positive) },
        )

        else -> DetailRow(answer.label, value = answer.value?.takeIf { it.isNotBlank() } ?: stringResource(Res.string.tasks_source_empty_answer))
    }
}
