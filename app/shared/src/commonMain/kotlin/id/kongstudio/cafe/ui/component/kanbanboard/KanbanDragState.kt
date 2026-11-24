package id.kongstudio.cafe.ui.component.kanbanboard

import androidx.compose.runtime.Stable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.unit.IntSize

/** Satu kartu yang sedang diseret; posisi dihitung dalam koordinat root layar. */
@Stable
internal class KanbanDragState<T : Any> {
    var item: T? by mutableStateOf(null)
        private set
    var fromColumn: String? = null
        private set
    var size: IntSize by mutableStateOf(IntSize.Zero)
        private set
    var pointer: Offset by mutableStateOf(Offset.Zero)
        private set

    private var grab: Offset = Offset.Zero

    val active: Boolean get() = item != null

    /** Pojok kiri atas kartu bayangan, mengikuti jari dengan titik pegang yang sama seperti saat ditekan. */
    val ghostTopLeft: Offset get() = pointer - grab

    fun start(item: T, column: String, cardTopLeft: Offset, cardSize: IntSize, grabOffset: Offset) {
        this.item = item
        fromColumn = column
        size = cardSize
        grab = grabOffset
        pointer = cardTopLeft + grabOffset
    }

    fun move(delta: Offset) {
        pointer += delta
    }

    fun clear() {
        item = null
        fromColumn = null
    }
}
