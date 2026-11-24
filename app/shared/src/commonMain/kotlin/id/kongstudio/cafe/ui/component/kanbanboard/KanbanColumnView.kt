package id.kongstudio.cafe.ui.component.kanbanboard

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectDragGesturesAfterLongPress
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.boundsInRoot
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.layout.positionInRoot
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.IntSize
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.theme.AppTheme

private const val DraggedCardAlpha = 0.3f

/** Panggilan gestur seret dari satu kartu ke papan induknya. */
internal class KanbanDragCallbacks<T>(
    val onStart: (item: T, columnKey: String, cardTopLeft: Offset, cardSize: IntSize, grab: Offset) -> Unit,
    val onMove: (delta: Offset) -> Unit,
    val onEnd: () -> Unit,
    val onCancel: () -> Unit,
)

/** Satu kolom papan: judul dengan penanda warna dan jumlah, lalu deretan kartu yang bisa digulir. */
@Composable
internal fun <T : Any> KanbanColumnView(
    column: KanbanColumn<T>,
    itemKey: (T) -> String,
    emptyText: String,
    highlighted: Boolean,
    draggingKey: String?,
    canDrag: (T) -> Boolean,
    drag: KanbanDragCallbacks<T>,
    onItemClick: (T) -> Unit,
    onBounds: (Rect) -> Unit,
    modifier: Modifier = Modifier,
    card: @Composable (T) -> Unit,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val shape = AppTheme.shapes.field

    Column(
        modifier = modifier
            .onGloballyPositioned { onBounds(it.boundsInRoot()) }
            .clip(shape)
            .background(colors.surface)
            .border(
                width = if (highlighted) AppTheme.sizes.borderThick else AppTheme.sizes.borderThin,
                color = if (highlighted) column.accent else colors.divider,
                shape = shape,
            ),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(spacing.md),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(spacing.sm),
        ) {
            Box(Modifier.size(spacing.sm).clip(AppTheme.shapes.pill).background(column.accent))
            BasicText(
                text = column.title,
                style = AppTheme.typography.label.copy(color = colors.content),
                modifier = Modifier.weight(1f),
            )
            StatusBadge(text = column.items.size.toString(), tone = BadgeTone.Neutral)
        }

        if (column.items.isEmpty()) {
            Notice(emptyText)
        } else {
            LazyColumn(
                contentPadding = PaddingValues(start = spacing.sm, end = spacing.sm, bottom = spacing.sm),
                verticalArrangement = Arrangement.spacedBy(spacing.sm),
            ) {
                items(column.items, key = { itemKey(it) }) { item ->
                    DraggableCard(
                        item = item,
                        columnKey = column.key,
                        enabled = canDrag(item),
                        dragging = draggingKey == itemKey(item),
                        drag = drag,
                        onClick = { onItemClick(item) },
                        content = card,
                    )
                }
            }
        }
    }
}

/** Kartu yang bisa diketuk, atau diseret setelah ditekan lama agar tidak bentrok dengan gulir kolom. */
@Composable
private fun <T : Any> DraggableCard(
    item: T,
    columnKey: String,
    enabled: Boolean,
    dragging: Boolean,
    drag: KanbanDragCallbacks<T>,
    onClick: () -> Unit,
    content: @Composable (T) -> Unit,
) {
    var topLeft by remember { mutableStateOf(Offset.Zero) }
    var size by remember { mutableStateOf(IntSize.Zero) }
    val currentDrag by rememberUpdatedState(drag)
    val currentItem by rememberUpdatedState(item)

    Box(
        modifier = Modifier
            .onGloballyPositioned {
                topLeft = it.positionInRoot()
                size = it.size
            }
            .alpha(if (dragging) DraggedCardAlpha else 1f)
            .pointerInput(enabled, columnKey) {
                if (!enabled) return@pointerInput
                detectDragGesturesAfterLongPress(
                    onDragStart = { grab -> currentDrag.onStart(currentItem, columnKey, topLeft, size, grab) },
                    onDrag = { change, amount ->
                        change.consume()
                        currentDrag.onMove(amount)
                    },
                    onDragEnd = { currentDrag.onEnd() },
                    onDragCancel = { currentDrag.onCancel() },
                )
            }
            .clickable(role = Role.Button, onClick = onClick),
    ) {
        content(item)
    }
}
