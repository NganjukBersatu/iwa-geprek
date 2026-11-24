package id.kongstudio.cafe.feature.cashier

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.core.time.BusinessDay
import id.kongstudio.cafe.feature.cashier.cart.CartPanel
import id.kongstudio.cafe.feature.cashier.cart.LineNoteSheet
import id.kongstudio.cafe.feature.cashier.cart.OrderIdentity
import id.kongstudio.cafe.feature.cashier.cart.OrderIdentityActions
import id.kongstudio.cafe.feature.printer.TabletMode
import id.kongstudio.cafe.feature.printer.printerSlotName
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.cashier_cart_hide
import id.kongstudio.cafe.resources.cashier_cart_show
import id.kongstudio.cafe.resources.cashier_clear_action
import id.kongstudio.cafe.resources.bill_ack
import id.kongstudio.cafe.resources.bill_added
import id.kongstudio.cafe.resources.bill_saved
import id.kongstudio.cafe.resources.bill_adding_banner
import id.kongstudio.cafe.resources.cashier_cart_restored
import id.kongstudio.cafe.resources.cashier_cart_restored_ack
import id.kongstudio.cafe.resources.cashier_incomplete
import id.kongstudio.cafe.resources.cashier_incomplete_retry
import id.kongstudio.cafe.resources.cashier_clear_message
import id.kongstudio.cafe.resources.cashier_clear_title
import id.kongstudio.cafe.resources.cashier_items_count
import id.kongstudio.cafe.resources.cashier_menu_empty
import id.kongstudio.cafe.resources.cashier_order_note_confirm_action
import id.kongstudio.cafe.resources.cashier_order_note_confirm_message
import id.kongstudio.cafe.resources.cashier_order_note_confirm_title
import id.kongstudio.cafe.resources.cashier_promo
import id.kongstudio.cafe.resources.cashier_search
import id.kongstudio.cafe.resources.cashier_status_ingredient
import id.kongstudio.cafe.resources.cashier_status_no_recipe
import id.kongstudio.cafe.resources.cashier_status_sold_out
import id.kongstudio.cafe.resources.nav_cashier
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.component.backhandler.PlatformBackHandler
import id.kongstudio.cafe.ui.component.cartbar.CartSummaryBar
import id.kongstudio.cafe.ui.component.chip.AppChip
import id.kongstudio.cafe.ui.component.confirmsheet.ConfirmSheet
import id.kongstudio.cafe.ui.component.failurestate.FailureState
import id.kongstudio.cafe.ui.component.iconbutton.AppIconButton
import id.kongstudio.cafe.ui.component.loadingstate.LoadingState
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.component.pagetitle.PageTitle
import id.kongstudio.cafe.ui.component.panelsurface.PanelSurface
import id.kongstudio.cafe.ui.component.productcard.BlockedTone
import id.kongstudio.cafe.ui.component.productcard.ProductCard
import id.kongstudio.cafe.ui.component.slidingpanel.PanelSide
import id.kongstudio.cafe.ui.component.statusbanner.BannerTone
import id.kongstudio.cafe.ui.component.statusbanner.StatusBanner
import id.kongstudio.cafe.ui.component.slidingpanel.SlidingPanel
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

@Composable
internal fun CashierScreen(
    viewModel: CashierViewModel,
    modifier: Modifier = Modifier,
    onOpenSession: (() -> Unit)? = null,
    openBillEnabled: Boolean = true,
) {
    val state by viewModel.state.collectAsState()
    val cart = viewModel.cart
    var cartOpen by rememberSaveable { mutableStateOf(false) }
    var cartHidden by rememberSaveable { mutableStateOf(true) }
    var cartExpanded by rememberSaveable { mutableStateOf(false) }
    var paying by rememberSaveable { mutableStateOf(false) }
    var choosing by remember { mutableStateOf<CashierItem?>(null) }
    var notingKey by remember { mutableStateOf<String?>(null) }
    var clearing by rememberSaveable { mutableStateOf(false) }
    var addingNote by remember { mutableStateOf<String?>(null) }
    val wide = AppTheme.windowSize.isWide

    val catalog = remember(state.items) { state.items.associateBy { it.id } }
    val lines = cart.lines(catalog)
    val today = BusinessDay.today()
    val promo = state.promoFor(lines, today)
    val discount = promo?.discountOf(lines, today) ?: 0
    val total = (lines.sumOf { it.subtotal } - discount).coerceAtLeast(0)
    val printerPaired by viewModel.printerPaired.collectAsState()
    val printerLinks by viewModel.printerLinks.collectAsState()
    val warnings = printerWarnings(lines, state.printPlan, printerPaired, printerLinks)

    PlatformBackHandler(enabled = cartOpen && !wide) { cartOpen = false }

    // Panel membuka sendiri saat item pertama masuk dan menutup saat keranjang kosong.
    val hasItems = cart.itemCount > 0
    LaunchedEffect(hasItems) {
        cartHidden = !hasItems
        if (!hasItems) cartExpanded = false
    }

    val onItemTap: (CashierItem) -> Unit = { item ->
        if (item.needsChoice) choosing = item else cart.add(item)
    }

    val cartPanel = @Composable { onBack: (() -> Unit)?, onToggleExpand: (() -> Unit)? ->
        CartPanel(
            lines = lines,
            total = total,
            identity = OrderIdentity(
                takeAway = state.takeAway,
                customerName = state.customerName,
                customerLinked = state.customerId != null,
                customerSuggestions = state.customerSuggestions,
                suggestionFailure = state.suggestionFailure,
                tableNo = state.tableNo,
                visitors = state.visitors,
                visitorCategoryId = state.visitorCategoryId,
                visitorGenderId = state.visitorGenderId,
                notes = state.notes,
                noteId = state.noteId,
                noteFailure = state.noteFailure,
            ),
            identityActions = OrderIdentityActions(
                onTakeAway = viewModel::setTakeAway,
                onCustomerName = viewModel::setCustomerName,
                onPickCustomer = viewModel::pickCustomer,
                onTableNo = viewModel::setTableNo,
                onVisitorCategory = viewModel::chooseVisitorCategory,
                onVisitorGender = viewModel::chooseVisitorGender,
                onNote = viewModel::chooseNote,
                onAddNote = { typed -> typed.trim().takeIf { it.isNotEmpty() }?.let { addingNote = it } },
            ),
            shiftOpen = state.shiftOpen,
            promos = state.promosToday(today),
            promo = promo,
            discount = discount,
            onPromo = viewModel::choosePromo,
            onIncrease = cart::increase,
            onDecrease = cart::decrease,
            onEditNote = { notingKey = it },
            onClear = { clearing = true },
            onPay = {
                viewModel.startPayment()
                paying = true
            },
            onBack = onBack,
            expanded = cartExpanded,
            onToggleExpand = onToggleExpand,
            onOpenSession = onOpenSession,
            printerWarnings = warnings,
            billReceipt = state.addingTo?.receipt,
            addingToBill = state.addingTo != null,
            savingBill = state.savingBill,
            onSaveBill = viewModel::saveBill,
            canSaveBill = openBillEnabled,
            onAddToBill = viewModel::addToBill,
            onCancelAdding = viewModel::cancelAdding,
        )
    }

    val failure = state.failure
    when {
        state.loading -> Box(modifier = modifier.fillMaxSize().padding(AppTheme.windowSize.pagePadding)) {
            LoadingState()
        }

        failure != null -> FailureState(
            failure = failure,
            onRetry = viewModel::load,
            modifier = modifier.fillMaxSize().padding(AppTheme.windowSize.pagePadding),
        )

        wide -> SlidingPanel(
            side = PanelSide.End,
            hidden = cartHidden,
            onHiddenChange = {
                cartHidden = it
                if (it) cartExpanded = false
            },
            panelWidth = AppTheme.sizes.sidePanelWidth + AppTheme.spacing.sm * 2,
            showHandle = false,
            expanded = cartExpanded,
            modifier = modifier,
            panel = {
                PanelSurface {
                    cartPanel(null) { cartExpanded = !cartExpanded }
                }
            },
        ) {
            MenuPane(
                state = state,
                cart = cart,
                onTap = onItemTap,
                onDecrease = cart::decreaseMenu,
                onCategory = viewModel::selectCategory,
                onRetryLoad = viewModel::load,
                onDismissRestored = viewModel::dismissRestoredNotice,
                onDismissBill = viewModel::dismissBillNotice,
                modifier = Modifier.fillMaxSize(),
                cartToggle = CartToggle(
                    hidden = cartHidden,
                    count = cart.itemCount,
                    onClick = {
                        cartHidden = !cartHidden
                        if (cartHidden) cartExpanded = false
                    },
                ),
            )
        }

        cartOpen -> Box(modifier = modifier.fillMaxSize()) {
            cartPanel({ cartOpen = false }, null)
        }

        else -> Column(modifier = modifier.fillMaxSize()) {
            MenuPane(
                state = state,
                cart = cart,
                onTap = onItemTap,
                onDecrease = cart::decreaseMenu,
                onCategory = viewModel::selectCategory,
                onRetryLoad = viewModel::load,
                onDismissRestored = viewModel::dismissRestoredNotice,
                onDismissBill = viewModel::dismissBillNotice,
                modifier = Modifier.weight(1f),
            )
            if (cart.itemCount > 0) {
                CartSummaryBar(
                    countLabel = stringResource(Res.string.cashier_items_count, cart.itemCount),
                    totalLabel = formatRupiah(total),
                    onClick = { cartOpen = true },
                    modifier = Modifier.padding(
                        horizontal = AppTheme.windowSize.pagePadding,
                        vertical = AppTheme.spacing.sm,
                    ),
                )
            }
        }
    }

    choosing?.let { item ->
        VariantSheet(
            item = item,
            onDismiss = { choosing = null },
            onConfirm = { variantIds, extras, note ->
                cart.add(item, variantIds, extras, note)
                choosing = null
            },
        )
    }

    notingKey?.let { key ->
        val line = lines.firstOrNull { it.key == key }
        if (line != null) {
            LineNoteSheet(
                title = line.item.name,
                note = line.note.orEmpty(),
                onDismiss = { notingKey = null },
                onSave = { text ->
                    cart.setNote(key, text)
                    notingKey = null
                },
            )
        }
    }

    if (clearing) {
        ConfirmSheet(
            title = stringResource(Res.string.cashier_clear_title),
            message = stringResource(Res.string.cashier_clear_message),
            confirmLabel = stringResource(Res.string.cashier_clear_action),
            destructive = true,
            onConfirm = {
                viewModel.clearOrder()
                clearing = false
            },
            onDismiss = { clearing = false },
        )
    }

    addingNote?.let { name ->
        ConfirmSheet(
            title = stringResource(Res.string.cashier_order_note_confirm_title),
            message = stringResource(Res.string.cashier_order_note_confirm_message, name),
            confirmLabel = stringResource(Res.string.cashier_order_note_confirm_action),
            onConfirm = {
                viewModel.addNote(name)
                addingNote = null
            },
            onDismiss = { addingNote = null },
        )
    }

    // Daftar metode dibekukan selama dialog terbuka: perubahan dari web tidak menggeser tombol di bawah jari kasir.
    val methodsWhilePaying = remember(paying) { state.methods }
    if (paying) {
        PaymentSheet(
            summary = PaymentSummary(lines = lines, promoName = promo?.name, discount = discount, total = total),
            methods = methodsWhilePaying,
            submitting = state.submitting,
            failure = state.submitFailure,
            placed = state.placed,
            placedMethod = state.placedMethod,
            print = ReceiptPrintView(
                printing = state.printing,
                reported = state.printReport != null,
                printedAny = state.printReport?.printedAny == true,
                unpaired = state.printReport?.unpaired?.map { printerSlotName(it, state.printPlan) }.orEmpty(),
                failed = state.printReport?.failed?.map { printerSlotName(it, state.printPlan) }.orEmpty(),
                fromHistory = state.printPlan?.mode == TabletMode.Cashier,
            ),
            tickets = TicketPrint(
                printing = state.ticketPrinting,
                printed = state.ticketsPrinted,
                failures = state.ticketFailures.map { printerSlotName(it, state.printPlan) },
                available = state.ticketSlots.isNotEmpty(),
                receiptFailure = state.receiptFailure,
            ),
            onPrintTickets = viewModel::printTickets,
            onReprint = viewModel::reprint,
            onConfirm = viewModel::submit,
            onDismiss = {
                paying = false
                viewModel.dismissPlaced()
                cartOpen = false
            },
        )
    }
}

private class CartToggle(val hidden: Boolean, val count: Int, val onClick: () -> Unit)

@Composable
private fun MenuPane(
    state: CashierUiState,
    cart: CartState,
    onTap: (CashierItem) -> Unit,
    onDecrease: (String) -> Unit,
    onCategory: (String) -> Unit,
    onRetryLoad: () -> Unit,
    onDismissRestored: () -> Unit,
    onDismissBill: () -> Unit,
    modifier: Modifier = Modifier,
    cartToggle: CartToggle? = null,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    var query by rememberSaveable { mutableStateOf("") }

    val categories = remember(state.items, state.bestsellerIds, state.promos) { state.categoryTabs() }
    val active = state.activeCategory
    val visible = remember(state.items, state.bestsellerIds, state.promos, state.category, query) { state.visibleItems(query) }
    val promoIds = remember(state.items, state.promos) { state.promoMenuIds(BusinessDay.today()) }
    val promoTag = stringResource(Res.string.cashier_promo)

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = AppTheme.windowSize.pagePadding),
    ) {
        Spacer(Modifier.height(spacing.lg))
        PageTitle(title = stringResource(Res.string.nav_cashier)) {
            cartToggle?.let { toggle ->
                AppIconButton(
                    icon = AppIcons.Cart,
                    contentDescription = stringResource(
                        if (toggle.hidden) Res.string.cashier_cart_show else Res.string.cashier_cart_hide,
                    ),
                    onClick = toggle.onClick,
                    tint = if (toggle.hidden) colors.content else colors.primary,
                    badge = toggle.count.takeIf { it > 0 }?.toString(),
                )
            }
        }
        state.billNotice?.let { notice ->
            StatusBanner(
                text = stringResource(if (notice.added) Res.string.bill_added else Res.string.bill_saved, notice.receipt.orEmpty()),
                tone = BannerTone.Info,
                actionLabel = stringResource(Res.string.bill_ack),
                onAction = onDismissBill,
            )
            Spacer(Modifier.height(spacing.md))
        }
        state.billFailure?.let { failure ->
            StatusBanner(
                text = failureText(failure),
                tone = BannerTone.Warning,
                actionLabel = stringResource(Res.string.bill_ack),
                onAction = onDismissBill,
            )
            Spacer(Modifier.height(spacing.md))
        }
        state.addingTo?.let { bill ->
            StatusBanner(
                text = stringResource(Res.string.bill_adding_banner, bill.receipt.orEmpty()),
                tone = BannerTone.Info,
            )
            Spacer(Modifier.height(spacing.md))
        }
        if (state.cartRestored) {
            StatusBanner(
                text = stringResource(Res.string.cashier_cart_restored),
                tone = BannerTone.Warning,
                actionLabel = stringResource(Res.string.cashier_cart_restored_ack),
                onAction = onDismissRestored,
            )
            Spacer(Modifier.height(spacing.md))
        }
        if (state.incomplete) {
            StatusBanner(
                text = stringResource(Res.string.cashier_incomplete),
                tone = BannerTone.Warning,
                actionLabel = stringResource(Res.string.cashier_incomplete_retry),
                onAction = onRetryLoad,
            )
            Spacer(Modifier.height(spacing.md))
        }
        AppTextField(
            value = query,
            onValueChange = { query = it },
            label = stringResource(Res.string.cashier_search),
            trailing = {
                AppIcon(
                    icon = AppIcons.Search,
                    tint = colors.contentMuted,
                    size = AppTheme.sizes.iconSmall,
                    modifier = Modifier.padding(end = spacing.md),
                )
            },
        )
        Spacer(Modifier.height(spacing.md))
        LazyRow(horizontalArrangement = Arrangement.spacedBy(spacing.sm)) {
            items(categories, key = { it }) { tab ->
                AppChip(label = categoryLabel(tab), selected = tab == active, onClick = { onCategory(tab) })
            }
        }

        if (visible.isEmpty()) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Notice(stringResource(Res.string.cashier_menu_empty))
            }
        } else {
            val soldOut = stringResource(Res.string.cashier_status_sold_out)
            val ingredient = stringResource(Res.string.cashier_status_ingredient)
            val noRecipe = stringResource(Res.string.cashier_status_no_recipe)

            LazyVerticalGrid(
                columns = GridCells.Adaptive(AppTheme.sizes.cardMinWidth),
                contentPadding = PaddingValues(top = spacing.md, bottom = spacing.lg),
                horizontalArrangement = Arrangement.spacedBy(spacing.sm),
                verticalArrangement = Arrangement.spacedBy(spacing.sm),
                modifier = Modifier.fillMaxSize(),
            ) {
                items(visible, key = { it.id }) { item ->
                    ProductCard(
                        name = item.name,
                        price = formatRupiah(item.price),
                        quantity = cart.quantityOf(item.id),
                        onAdd = { onTap(item) },
                        onDecrease = { onDecrease(item.id) },
                        imageUrl = item.imageUrl,
                        unavailableLabel = when (item.status) {
                            ItemStatus.Ready -> null
                            ItemStatus.SoldOut -> soldOut
                            ItemStatus.IngredientOut -> ingredient
                            ItemStatus.NoRecipe -> noRecipe
                        },
                        unavailableTone = when (item.status) {
                            ItemStatus.IngredientOut -> BlockedTone.Warning
                            ItemStatus.NoRecipe -> BlockedTone.Caution
                            ItemStatus.Ready, ItemStatus.SoldOut -> BlockedTone.Danger
                        },
                        stepper = !item.needsChoice,
                        tag = promoTag.takeIf { item.id in promoIds },
                    )
                }
            }
        }
    }
}
