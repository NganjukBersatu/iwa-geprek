package id.kongstudio.cafe.ui.component.movementdetailsheet

import androidx.compose.runtime.Composable
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.format.whenLabel
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.common_note
import id.kongstudio.cafe.resources.movement_cause
import id.kongstudio.cafe.resources.movement_kind
import id.kongstudio.cafe.resources.movement_quantity
import id.kongstudio.cafe.resources.movement_user
import id.kongstudio.cafe.resources.movement_time
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.detailcard.DetailCard
import org.jetbrains.compose.resources.stringResource

/** Rincian satu catatan stok (barang masuk, rusak, RnD, atau jual-ulang) yang dibuka dari barisnya; [actions] untuk aksi bagi yang berhak. */
@Composable
fun MovementDetailSheet(
    title: String,
    quantity: String,
    cause: String?,
    note: String?,
    userName: String?,
    createdAt: String,
    onDismiss: () -> Unit,
    kind: String? = null,
    actions: @Composable () -> Unit = {},
) {
    val written = DateTimeFormat.stamp(createdAt)?.let { whenLabel(it) }
    AppBottomSheet(title = title, onDismiss = onDismiss) {
        DetailCard(
            rows = listOf(
                stringResource(Res.string.movement_kind) to kind,
                stringResource(Res.string.movement_quantity) to quantity,
                stringResource(Res.string.movement_cause) to cause,
                stringResource(Res.string.common_note) to note,
                stringResource(Res.string.movement_user) to userName,
                stringResource(Res.string.movement_time) to written,
            ),
        )
        // Lembar ditutup lewat tombol silang atau kembali, jadi tidak ada tombol Tutup yang menyaingi aksi.
        actions()
    }
}
