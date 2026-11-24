package id.kongstudio.cafe.ui.component.detaillist

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.ui.component.divideditems.DividedItems
import id.kongstudio.cafe.ui.component.listcard.ListCard

/** Kartu rincian: tiap elemen [rows] biasanya satu `DetailRow`, dipisah garis. */
@Composable
fun DetailList(
    rows: List<@Composable () -> Unit>,
    modifier: Modifier = Modifier,
) {
    ListCard(modifier = modifier) { DividedItems(rows) { it() } }
}
