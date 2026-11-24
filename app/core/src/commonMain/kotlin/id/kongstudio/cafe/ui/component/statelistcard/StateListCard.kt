package id.kongstudio.cafe.ui.component.statelistcard

import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.loadable.Loadable
import id.kongstudio.cafe.ui.component.notice.Notice

/** Kartu daftar yang menangani tiga keadaannya sendiri: memuat (kerangka), kosong (keterangan), dan berisi ([content]). */
@Composable
fun StateListCard(
    loading: Boolean,
    empty: Boolean,
    emptyText: String,
    modifier: Modifier = Modifier,
    skeletonRows: Int = 3,
    content: @Composable ColumnScope.() -> Unit,
) {
    Loadable(loading = loading, modifier = modifier, rows = skeletonRows) {
        if (empty) ListCard { Notice(emptyText) } else ListCard(content = content)
    }
}
