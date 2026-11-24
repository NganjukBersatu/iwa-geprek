package id.kongstudio.cafe.ui.component.listcard

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import id.kongstudio.cafe.ui.theme.AppTheme

/** Wadah putih berbingkai untuk deretan baris; pemisah antarbaris dipasang pemanggil. */
@Composable
fun ListCard(
    modifier: Modifier = Modifier,
    content: @Composable ColumnScope.() -> Unit,
) {
    val shape = AppTheme.shapes.field

    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(shape)
            .background(AppTheme.colors.surface)
            .border(AppTheme.sizes.borderThin, AppTheme.colors.divider, shape),
        content = content,
    )
}
