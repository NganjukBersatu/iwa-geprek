package id.kongstudio.cafe.ui.component.permissiongate

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.appdialog.AppDialog
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.divideditems.DividedItems
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.successstate.SuccessState
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons

class PermissionGateItem(
    val title: String,
    val description: String,
    val statusText: String,
    val tone: BadgeTone,
    val onClick: (() -> Unit)? = null,
)

/** Modal tengah yang tidak bisa ditutup pengguna; pemanggil menutupnya lewat [visible] false. */
@Composable
fun PermissionGate(
    title: String,
    message: String,
    items: List<PermissionGateItem>,
    actionLabel: String,
    onAction: () -> Unit,
    onClosed: () -> Unit,
    modifier: Modifier = Modifier,
    visible: Boolean = true,
    completed: Boolean = false,
    completedTitle: String = "",
    completedMessage: String = "",
) {
    val spacing = AppTheme.spacing

    AppDialog(
        title = title,
        onDismiss = onClosed,
        modifier = modifier,
        dismissible = false,
        visible = visible,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .verticalScroll(rememberScrollState())
                .padding(spacing.lg),
            verticalArrangement = Arrangement.spacedBy(spacing.lg),
        ) {
            if (completed) {
                SuccessState(title = completedTitle, message = completedMessage, icon = AppIcons.Checklist)
            } else {
                BasicText(
                    text = message,
                    style = AppTheme.typography.caption.copy(color = AppTheme.colors.contentMuted),
                )
                ListCard {
                    DividedItems(items) { item ->
                        ListRow(
                            title = item.title,
                            caption = item.description,
                            trailing = { StatusBadge(text = item.statusText, tone = item.tone) },
                            onClick = item.onClick,
                        )
                    }
                }
                PrimaryButton(text = actionLabel, onClick = onAction)
            }
        }
    }
}
