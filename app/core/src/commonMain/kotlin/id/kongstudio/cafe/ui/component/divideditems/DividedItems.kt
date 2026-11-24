package id.kongstudio.cafe.ui.component.divideditems

import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.runtime.Composable
import id.kongstudio.cafe.ui.component.divider.AppDivider

/** Menyusun [items] ke bawah dengan garis pemisah antarbaris; dipakai di dalam `ListCard`. */
@Composable
fun <T> ColumnScope.DividedItems(
    items: List<T>,
    row: @Composable (T) -> Unit,
) {
    items.forEachIndexed { index, item ->
        if (index > 0) AppDivider()
        row(item)
    }
}
