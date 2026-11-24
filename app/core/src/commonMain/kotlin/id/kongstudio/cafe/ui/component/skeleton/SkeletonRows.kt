package id.kongstudio.cafe.ui.component.skeleton

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.common_loading
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

/** Kerangka baris pilihan selebar penuh, setinggi satu baris daftar pilihan, untuk daftar pilihan yang sedang dimuat. */
@Composable
fun SkeletonRows(count: Int, modifier: Modifier = Modifier) {
    val spacing = AppTheme.spacing
    val description = stringResource(Res.string.common_loading)
    Column(
        modifier = modifier.fillMaxWidth().semantics { contentDescription = description },
        verticalArrangement = Arrangement.spacedBy(spacing.sm),
    ) {
        repeat(count) {
            SkeletonBlock(modifier = Modifier.fillMaxWidth().height(spacing.touchTarget))
        }
    }
}
