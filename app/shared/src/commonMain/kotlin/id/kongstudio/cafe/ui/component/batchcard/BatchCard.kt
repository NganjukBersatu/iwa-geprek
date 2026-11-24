package id.kongstudio.cafe.ui.component.batchcard

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import id.kongstudio.cafe.ui.component.taskcard.TaskCard
import id.kongstudio.cafe.ui.component.taskcard.TaskCardTone
import id.kongstudio.cafe.ui.theme.icon.AppIcons

/** Kartu tugas berulang: bertombol [fillLabel] selama belum diisi, lalu menampilkan [doneLabel] dengan nama tugasnya setelah selesai; [tone], [icon], dan [tagLabel] membedakan jenisnya, [note] menyebut siapa yang mengisi. */
@Composable
fun BatchCard(
    title: String,
    rangeLabel: String,
    completed: Boolean,
    tagLabel: String,
    fillLabel: String,
    doneLabel: String,
    onFill: () -> Unit,
    modifier: Modifier = Modifier,
    icon: ImageVector = AppIcons.UsersGroup,
    note: String? = null,
    tone: TaskCardTone = TaskCardTone.Green,
    /** Membuka pilihan perbaiki, batalkan, atau hapus pada kartu yang sudah selesai; kosong berarti kartu tidak bisa diketuk. */
    onManage: (() -> Unit)? = null,
    manageLabel: String? = null,
) {
    if (completed) {
        TaskCard(
            title = doneLabel,
            tone = tone,
            icon = icon,
            completed = true,
            modifier = modifier,
            caption = "$title · $rangeLabel",
            actionLabel = manageLabel.takeIf { onManage != null },
            onAction = onManage,
            onClick = onManage,
        )
        return
    }
    TaskCard(
        title = title,
        tone = tone,
        icon = icon,
        completed = false,
        modifier = modifier,
        caption = rangeLabel,
        note = note,
        tagLabel = tagLabel,
        actionLabel = fillLabel,
        onAction = onFill,
    )
}
