package id.kongstudio.cafe.feature.cashier.cart

import androidx.compose.foundation.layout.Arrangement
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.apptext.AppText
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.feature.cashier.CartLine
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.cashier_line_note
import id.kongstudio.cafe.resources.cashier_note_edit
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.component.iconbutton.AppIconButton
import id.kongstudio.cafe.ui.component.quantitystepper.QuantityStepper
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

/** Satu baris pesanan: nama, pilihan varian/ekstra, catatan menu yang ditandai sendiri, subtotal, tombol catatan, dan pengatur jumlah. */
@Composable
internal fun CartLineRow(
    line: CartLine,
    onIncrease: () -> Unit,
    onDecrease: () -> Unit,
    onEditNote: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing

    Row(
        modifier = modifier.fillMaxWidth().padding(vertical = spacing.sm),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(spacing.sm),
    ) {
        Column(modifier = Modifier.weight(1f)) {
            AppText(
                text = line.item.name,
                role = TextRole.Body,
                color = colors.content,
            )
            if (line.details.isNotEmpty()) {
                AppText(
                    text = line.details.joinToString(", "),
                    role = TextRole.Label,
                    color = colors.contentMuted,
                )
            }
            line.note?.let { note ->
                Row(
                    verticalAlignment = Alignment.Top,
                    horizontalArrangement = Arrangement.spacedBy(spacing.xs),
                ) {
                    AppIcon(icon = AppIcons.FileText, tint = colors.primary, size = AppTheme.sizes.iconSmall)
                    AppText(
                        text = stringResource(Res.string.cashier_line_note, note),
                        role = TextRole.Label,
                        color = colors.primary,
                    )
                }
            }
            AppText(
                text = formatRupiah(line.subtotal),
                role = TextRole.Label,
                color = colors.contentMuted,
            )
        }
        AppIconButton(
            icon = AppIcons.FileText,
            contentDescription = stringResource(Res.string.cashier_note_edit),
            onClick = onEditNote,
            tint = colors.primary,
        )
        QuantityStepper(
            quantity = line.quantity,
            onDecrease = onDecrease,
            onIncrease = onIncrease,
        )
    }
}
