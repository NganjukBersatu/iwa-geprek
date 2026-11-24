package id.kongstudio.cafe.feature.activity

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.format.whenLabel
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.activity_filter_label
import id.kongstudio.cafe.resources.dashboard_empty_history
import id.kongstudio.cafe.ui.component.choicerow.ChoiceRow
import id.kongstudio.cafe.ui.component.failurestate.FailureState
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.pagedlistcard.PagedListCard
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

private const val SkeletonRows = 4

/** Halaman Riwayat: penyaring jenis di atas, lalu daftar aktivitas karyawan dari semua perangkat. */
@Composable
internal fun ActivityScreen(
    state: ActivityUiState,
    onSelectGroup: (ActivityGroup) -> Unit,
    onPageChange: (Int) -> Unit,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val spacing = AppTheme.spacing
    val groups = ActivityGroup.entries
    val failure = state.failure
    val page = state.page.coerceAtMost((state.pageCount - 1).coerceAtLeast(0))

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
                .padding(bottom = spacing.xl),
            verticalArrangement = Arrangement.spacedBy(spacing.md),
        ) {
            ChoiceRow(
                label = stringResource(Res.string.activity_filter_label),
                options = groups.map { it.label() },
                selectedIndex = groups.indexOf(state.group),
                onSelect = { onSelectGroup(groups[it]) },
            )
            if (failure != null) {
                ListCard { FailureState(failure = failure, onRetry = onRetry) }
            } else {
                PagedListCard(
                    items = state.events.drop(page * ActivityPageSize).take(ActivityPageSize),
                    page = page,
                    pageCount = state.pageCount,
                    onPageChange = onPageChange,
                    emptyText = stringResource(Res.string.dashboard_empty_history),
                    loading = state.loading,
                    skeletonRows = SkeletonRows,
                ) { event ->
                    ListRow(
                        title = event.title(),
                        detail = event.detail(),
                        caption = whenLabel(event.at),
                        leading = { IconBadge(event.icon) },
                    )
                }
            }
        }
    }
}
