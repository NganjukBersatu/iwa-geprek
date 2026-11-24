package id.kongstudio.cafe.feature.sop

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.sop_branch_only
import id.kongstudio.cafe.resources.sop_empty
import id.kongstudio.cafe.resources.sop_read_not_sent
import id.kongstudio.cafe.resources.sop_new
import id.kongstudio.cafe.resources.sop_slide_count
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.divideditems.DividedItems
import id.kongstudio.cafe.ui.component.failurestate.FailureState
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.component.statelistcard.StateListCard
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

@Composable
internal fun SopListScreen(
    state: SopUiState,
    onOpen: (SopSummary) -> Unit,
    onRetry: () -> Unit,
    onRetryRead: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val spacing = AppTheme.spacing

    Box(modifier = modifier.fillMaxSize(), contentAlignment = Alignment.TopCenter) {
        LazyColumn(
            modifier = Modifier.widthIn(max = AppTheme.sizes.contentMaxWidth).fillMaxHeight(),
            contentPadding = PaddingValues(
                horizontal = AppTheme.windowSize.pagePadding,
                vertical = spacing.lg,
            ),
            verticalArrangement = Arrangement.spacedBy(spacing.sm),
        ) {
            state.openFailure?.let { failure -> item { FailureState(failure = failure) } }
            state.markFailure?.let { failure ->
                item { Notice(stringResource(Res.string.sop_read_not_sent)) }
                item { FailureState(failure = failure, onRetry = onRetryRead) }
            }

            val failure = state.failure
            if (failure != null) {
                item { FailureState(failure = failure, onRetry = onRetry) }
            } else {
                item {
                    StateListCard(
                        loading = state.loading,
                        empty = state.items.isEmpty(),
                        emptyText = stringResource(Res.string.sop_empty),
                    ) {
                        DividedItems(state.items) { item ->
                            ListRow(
                                title = item.title,
                                detail = item.outletName?.let { stringResource(Res.string.sop_branch_only, it) },
                                caption = stringResource(Res.string.sop_slide_count, item.slideCount.toString()),
                                onClick = { onOpen(item) },
                                leading = { IconBadge(AppIcons.Book) },
                                trailing = {
                                    if (state.isNew(item)) {
                                        StatusBadge(text = stringResource(Res.string.sop_new), tone = BadgeTone.Positive)
                                    }
                                },
                            )
                        }
                    }
                }
            }
        }
    }
}
