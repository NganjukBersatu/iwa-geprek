package id.kongstudio.cafe.feature.attendance

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.runtime.Composable
import id.kongstudio.cafe.core.format.whenLabel
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.attendance_notice_ack
import id.kongstudio.cafe.resources.attendance_notice_caption
import id.kongstudio.cafe.resources.attendance_notice_title
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.divideditems.DividedItems
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

/** Daftar absen yang ditutup otomatis oleh sistem, dengan tombol untuk menandainya sudah dibaca. */
@Composable
internal fun AutoCloseNotices(notices: List<AutoCloseNotice>, acknowledging: Boolean, onAcknowledge: () -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm)) {
        ListCard {
            DividedItems(notices) { notice ->
                ListRow(
                    title = stringResource(
                        Res.string.attendance_notice_title,
                        notice.clockIn?.let { whenLabel(it) }.orEmpty(),
                    ),
                    caption = notice.clockOut?.let {
                        stringResource(Res.string.attendance_notice_caption, whenLabel(it))
                    },
                )
            }
        }
        PrimaryButton(
            text = stringResource(Res.string.attendance_notice_ack),
            onClick = onAcknowledge,
            loading = acknowledging,
        )
    }
}
