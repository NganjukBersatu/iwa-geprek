package id.kongstudio.cafe.feature.leaveovertime

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.leave_overtime_tab_leave
import id.kongstudio.cafe.resources.leave_overtime_tab_overtime
import id.kongstudio.cafe.ui.component.segmentedcontrol.SegmentedControl
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

/** Halaman Izin & Lembur: pilihan Izin atau Lembur di atas, isi bagian terpilih di bawahnya. */
@Composable
internal fun LeaveOvertimePage(
    selectedIndex: Int,
    onSelect: (Int) -> Unit,
    leave: @Composable () -> Unit,
    overtime: @Composable () -> Unit,
    modifier: Modifier = Modifier,
) {
    Box(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = AppTheme.windowSize.pagePadding),
        contentAlignment = Alignment.TopCenter,
    ) {
        Column(
            modifier = Modifier
                .widthIn(max = AppTheme.sizes.contentMaxWidth)
                .verticalScroll(rememberScrollState())
                .padding(bottom = AppTheme.spacing.xl),
            verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md),
        ) {
            SegmentedControl(
                options = listOf(
                    stringResource(Res.string.leave_overtime_tab_leave),
                    stringResource(Res.string.leave_overtime_tab_overtime),
                ),
                selectedIndex = selectedIndex,
                onSelect = onSelect,
            )
            if (selectedIndex == 0) leave() else overtime()
        }
    }
}
