package id.kongstudio.cafe.ui.component.codelegend

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import id.kongstudio.cafe.ui.component.codebadge.CodeBadge
import id.kongstudio.cafe.ui.component.divideditems.DividedItems
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.listrow.ListRow

class CodeLegendItem(
    val code: String,
    val color: Color?,
    val title: String,
    val detail: String? = null,
    val caption: String? = null,
)

/** Daftar arti tiap kode, satu baris per kode: keterangan di kiri, lencana berwarna di kanan. */
@Composable
fun CodeLegend(
    items: List<CodeLegendItem>,
    modifier: Modifier = Modifier,
) {
    ListCard(modifier = modifier) {
        DividedItems(items) { item ->
            ListRow(
                title = item.title,
                detail = item.detail,
                caption = item.caption,
                trailing = { CodeBadge(text = item.code, color = item.color) },
            )
        }
    }
}
