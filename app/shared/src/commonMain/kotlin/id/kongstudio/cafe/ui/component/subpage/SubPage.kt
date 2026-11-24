package id.kongstudio.cafe.ui.component.subpage

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.ui.component.backhandler.PlatformBackHandler
import id.kongstudio.cafe.ui.component.subpageheader.HeaderBack
import id.kongstudio.cafe.ui.component.subpageheader.HeaderWidth
import id.kongstudio.cafe.ui.component.subpageheader.SubPageHeader
import id.kongstudio.cafe.ui.theme.AppTheme

/**
 * Halaman turunan tablet satu kolom di bawah [SubPageHeader], selebar layar dengan jarak tepi halaman seperti detail stasiun dan pesanan kasir;
 * tombol kembali sistem ikut menutup halaman kecuali [canLeave] false, misalnya selama menyimpan.
 */
@Composable
fun SubPage(
    title: String,
    backLabel: String,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
    canLeave: Boolean = true,
    content: @Composable ColumnScope.() -> Unit,
) {
    val spacing = AppTheme.spacing
    val leave = { if (canLeave) onBack() }
    PlatformBackHandler(enabled = true, onBack = leave)

    Column(modifier = modifier.fillMaxSize()) {
        SubPageHeader(title = title, back = HeaderBack(backLabel, leave), width = HeaderWidth.Page)
        Column(
            modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(AppTheme.windowSize.pagePadding),
            verticalArrangement = Arrangement.spacedBy(spacing.md),
            content = content,
        )
    }
}
