package id.kongstudio.cafe.ui.component.pageframe

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyListScope
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.ui.theme.AppTheme

private const val WideContentFactor = 2

/** Bingkai halaman operasional: kolom bergulir di tengah dengan lebar, padding, dan jarak antarbagian yang seragam. */
@Composable
fun PageFrame(
    modifier: Modifier = Modifier,
    content: LazyListScope.() -> Unit,
) {
    Box(modifier = modifier.fillMaxSize(), contentAlignment = Alignment.TopCenter) {
        LazyColumn(
            modifier = Modifier
                .widthIn(max = AppTheme.sizes.contentMaxWidth * WideContentFactor)
                .fillMaxHeight(),
            contentPadding = PaddingValues(horizontal = AppTheme.windowSize.pagePadding, vertical = AppTheme.spacing.lg),
            verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md),
            content = content,
        )
    }
}
