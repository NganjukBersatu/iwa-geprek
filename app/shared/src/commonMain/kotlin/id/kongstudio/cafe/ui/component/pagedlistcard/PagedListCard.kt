package id.kongstudio.cafe.ui.component.pagedlistcard

import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.pagination_range
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.divideditems.DividedItems
import id.kongstudio.cafe.ui.component.divider.AppDivider
import id.kongstudio.cafe.ui.component.pagination.Pagination
import id.kongstudio.cafe.ui.component.statelistcard.StateListCard
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

/** Posisi halaman untuk keterangan "Menampilkan a–b dari n": [page] berbasis nol, [pageSize] ukuran halaman, [total] seluruh baris. */
class PageRange(val page: Int, val pageSize: Int, val total: Int)

/**
 * Kartu daftar berhalaman: [items] adalah isi halaman yang sedang tampil; kerangka, keadaan kosong, garis pemisah,
 * keterangan jumlah bila [range] diisi, dan pengatur halaman (hanya bila [pageCount] > 1) ditangani di sini.
 */
@Composable
fun <T> PagedListCard(
    items: List<T>,
    page: Int,
    pageCount: Int,
    onPageChange: (Int) -> Unit,
    emptyText: String,
    modifier: Modifier = Modifier,
    loading: Boolean = false,
    skeletonRows: Int = 3,
    range: PageRange? = null,
    row: @Composable (T) -> Unit,
) {
    StateListCard(
        loading = loading,
        empty = items.isEmpty(),
        emptyText = emptyText,
        modifier = modifier,
        skeletonRows = skeletonRows,
    ) {
        DividedItems(items, row)
        if (range != null) {
            val first = range.page * range.pageSize + 1
            val last = (first + items.size - 1).coerceAtMost(range.total.coerceAtLeast(first))
            AppDivider()
            AppText(
                text = stringResource(Res.string.pagination_range, first, last, range.total.coerceAtLeast(last)),
                role = TextRole.Caption,
                color = AppTheme.colors.contentMuted,
                modifier = Modifier.padding(horizontal = AppTheme.spacing.md, vertical = AppTheme.spacing.sm),
            )
        }
        if (pageCount > 1) {
            AppDivider()
            Pagination(
                page = page.coerceIn(0, pageCount - 1),
                pageCount = pageCount,
                onPageChange = onPageChange,
            )
        }
    }
}
