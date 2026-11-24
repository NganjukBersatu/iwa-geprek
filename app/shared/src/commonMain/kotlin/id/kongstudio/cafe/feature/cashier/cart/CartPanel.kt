package id.kongstudio.cafe.feature.cashier.cart

import id.kongstudio.cafe.resources.back_to_menu
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.apptext.AppText
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.GridItemSpan
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.feature.cashier.CartLine
import id.kongstudio.cafe.feature.cashier.CashierPromo
import id.kongstudio.cafe.feature.cashier.PrinterWarning
import id.kongstudio.cafe.feature.cashier.PrinterWarningBanner
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.cashier_discount
import id.kongstudio.cafe.resources.bill_add_to
import id.kongstudio.cafe.resources.bill_cancel_adding
import id.kongstudio.cafe.resources.bill_promo_not_kept
import id.kongstudio.cafe.resources.bill_save
import id.kongstudio.cafe.resources.cashier_no_promo
import id.kongstudio.cafe.resources.cashier_promo
import id.kongstudio.cafe.ui.component.choiceflow.ChoiceFlow
import id.kongstudio.cafe.resources.cashier_cart_expand
import id.kongstudio.cafe.resources.cashier_cart_shrink
import id.kongstudio.cafe.resources.cashier_clear
import id.kongstudio.cafe.resources.cashier_no_shift
import id.kongstudio.cafe.resources.cashier_order_empty
import id.kongstudio.cafe.resources.cashier_order_title
import id.kongstudio.cafe.resources.cashier_pay
import id.kongstudio.cafe.resources.cashier_total
import id.kongstudio.cafe.resources.session_open
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.secondarybutton.ButtonTone
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.divider.AppDivider
import id.kongstudio.cafe.ui.component.iconbutton.AppIconButton
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.component.subpageheader.HeaderBack
import id.kongstudio.cafe.ui.component.subpageheader.SubPageHeader
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

/** Isi pesanan: identitas, baris, total, dan tombol bayar, dengan [onBack] hanya untuk halaman penuh dan [onToggleExpand] menampilkan tombol lebarkan. */
@Composable
internal fun CartPanel(
    lines: List<CartLine>,
    total: Long,
    identity: OrderIdentity,
    identityActions: OrderIdentityActions,
    shiftOpen: Boolean,
    promos: List<CashierPromo>,
    promo: CashierPromo?,
    discount: Long,
    onPromo: (String?) -> Unit,
    onIncrease: (String) -> Unit,
    onDecrease: (String) -> Unit,
    onEditNote: (String) -> Unit,
    onClear: () -> Unit,
    onPay: () -> Unit,
    modifier: Modifier = Modifier,
    /** Bill yang sedang ditambah menunya; promo dan pembayaran bukan urusan keranjang ini. */
    billReceipt: String? = null,
    addingToBill: Boolean = false,
    savingBill: Boolean = false,
    onSaveBill: () -> Unit = {},
    /** Tombol Simpan Bill hanya ada selama Open Bill menyala di tablet ini. */
    canSaveBill: Boolean = true,
    onAddToBill: () -> Unit = {},
    onCancelAdding: () -> Unit = {},
    onBack: (() -> Unit)? = null,
    expanded: Boolean = false,
    onToggleExpand: (() -> Unit)? = null,
    onOpenSession: (() -> Unit)? = null,
    printerWarnings: List<PrinterWarning> = emptyList(),
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val wide = AppTheme.windowSize.isWide

    Column(modifier = modifier.fillMaxSize()) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            SubPageHeader(
                title = stringResource(Res.string.cashier_order_title),
                back = onBack?.let { HeaderBack(stringResource(Res.string.back_to_menu), it) },
                // Panel samping bersudut bulat: tanpa jarak, judul menempel di lengkungan.
                modifier = (if (wide) Modifier.padding(start = spacing.md, top = spacing.md, bottom = spacing.sm) else Modifier)
                    .weight(1f),
            )
            onToggleExpand?.let {
                AppIconButton(
                    icon = if (expanded) AppIcons.Shrink else AppIcons.Expand,
                    contentDescription = stringResource(
                        if (expanded) Res.string.cashier_cart_shrink else Res.string.cashier_cart_expand,
                    ),
                    onClick = it,
                )
            }
        }
        AppDivider()

        LazyVerticalGrid(
            columns = if (expanded) GridCells.Adaptive(AppTheme.sizes.sidePanelWidth) else GridCells.Fixed(1),
            modifier = Modifier.weight(1f).fillMaxWidth(),
            contentPadding = PaddingValues(horizontal = spacing.md, vertical = spacing.sm),
            verticalArrangement = Arrangement.spacedBy(spacing.xs),
            horizontalArrangement = Arrangement.spacedBy(spacing.sm),
        ) {
            // Jenis pesanan tetap di atas: lupa memilih Take Away merusak data kanal, jadi tidak boleh tersembunyi di bawah.
            item(span = { GridItemSpan(maxLineSpan) }) {
                OrderTypeField(identity = identity, actions = identityActions, modifier = Modifier.padding(bottom = spacing.sm))
            }
            if (lines.isEmpty()) {
                item(span = { GridItemSpan(maxLineSpan) }) {
                    AppText(
                        text = stringResource(Res.string.cashier_order_empty),
                        role = TextRole.Body,
                        color = colors.contentMuted,
                        modifier = Modifier.padding(vertical = spacing.lg),
                    )
                }
            } else {
                items(lines, key = { it.key }) { line ->
                    CartLineRow(
                        line = line,
                        onIncrease = { onIncrease(line.key) },
                        onDecrease = { onDecrease(line.key) },
                        onEditNote = { onEditNote(line.key) },
                    )
                }
                if (promos.isNotEmpty()) {
                    item(span = { GridItemSpan(maxLineSpan) }) {
                        // Opsi pertama "Tanpa promo"; satu pesanan hanya memakai satu promo, dan nama promo dari data bisa panjang sehingga chip boleh turun baris.
                        val options = listOf(stringResource(Res.string.cashier_no_promo)) + promos.map { it.name }
                        val selected = promo?.let { chosen -> promos.indexOfFirst { it.id == chosen.id }.takeIf { it >= 0 }?.plus(1) } ?: 0
                        ChoiceFlow(
                            label = stringResource(Res.string.cashier_promo),
                            options = options,
                            selectedIndex = selected,
                            onSelect = { index -> onPromo(promos.getOrNull(index - 1)?.id) },
                            modifier = Modifier.padding(top = spacing.sm),
                        )
                    }
                }
                item(span = { GridItemSpan(maxLineSpan) }) {
                    // Bayar satu-satunya tombol utama; aksi menghapus keranjang memakai tombol pendamping bernada bahaya (rules 6.8.2).
                    SecondaryButton(
                        text = stringResource(Res.string.cashier_clear),
                        onClick = onClear,
                        tone = ButtonTone.Danger,
                        modifier = Modifier.padding(vertical = spacing.sm),
                    )
                }
            }
            // Identitas semuanya opsional, jadi di bawah item dan promo: yang dipilih kasir tidak tertutup formulir.
            item(span = { GridItemSpan(maxLineSpan) }) {
                OrderHeader(
                    identity = identity,
                    actions = identityActions,
                    modifier = Modifier.padding(top = spacing.sm),
                )
            }
        }

        AppDivider()
        Column(
            modifier = Modifier.fillMaxWidth().padding(spacing.md),
            verticalArrangement = Arrangement.spacedBy(spacing.md),
        ) {
            printerWarnings.forEach { PrinterWarningBanner(it) }
            if (!shiftOpen) {
                Notice(stringResource(Res.string.cashier_no_shift))
                onOpenSession?.let { SecondaryButton(text = stringResource(Res.string.session_open), onClick = it) }
            }
            if (promo != null && discount > 0) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    AppText(
                        text = stringResource(Res.string.cashier_discount, promo.name),
                        role = TextRole.Body,
                        color = colors.contentMuted,
                    )
                    AppText(
                        text = "-${formatRupiah(discount)}",
                        role = TextRole.Body,
                        color = colors.contentMuted,
                    )
                }
            }
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                AppText(
                    text = stringResource(Res.string.cashier_total),
                    role = TextRole.Body,
                    color = colors.contentMuted,
                )
                AppText(
                    text = formatRupiah(total),
                    role = TextRole.Title,
                    color = colors.content,
                )
            }
            if (addingToBill) {
                PrimaryButton(
                    text = stringResource(Res.string.bill_add_to, billReceipt.orEmpty()),
                    onClick = onAddToBill,
                    enabled = lines.isNotEmpty() && !savingBill,
                )
                SecondaryButton(text = stringResource(Res.string.bill_cancel_adding), onClick = onCancelAdding)
            } else {
                if (promo != null && lines.isNotEmpty()) {
                    AppText(text = stringResource(Res.string.bill_promo_not_kept), role = TextRole.Caption, color = colors.contentMuted)
                }
                Row(horizontalArrangement = Arrangement.spacedBy(spacing.sm)) {
                    if (canSaveBill) {
                        SecondaryButton(
                            text = stringResource(Res.string.bill_save),
                            onClick = onSaveBill,
                            enabled = lines.isNotEmpty() && shiftOpen && !savingBill,
                            modifier = Modifier.weight(1f),
                        )
                    }
                    PrimaryButton(
                        text = stringResource(Res.string.cashier_pay),
                        onClick = onPay,
                        enabled = lines.isNotEmpty() && shiftOpen && !savingBill,
                        modifier = Modifier.weight(1f),
                    )
                }
            }
        }
    }
}
