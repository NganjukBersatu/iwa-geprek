package id.kongstudio.cafe.ui.component.detailcard

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.ui.component.detaillist.DetailList
import id.kongstudio.cafe.ui.component.detailrow.DetailRow

/** Kartu rincian dari pasangan label dan nilai; baris bernilai kosong atau null dilewati. */
@Composable
fun DetailCard(
    rows: List<Pair<String, String?>>,
    modifier: Modifier = Modifier,
) {
    val shown = rows.filter { !it.second.isNullOrBlank() }
    if (shown.isEmpty()) return
    DetailList(
        rows = shown.map { (label, value) -> { DetailRow(label = label, value = value.orEmpty()) } },
        modifier = modifier,
    )
}
