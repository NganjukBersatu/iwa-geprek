package id.kongstudio.cafe.feature.operational

import id.kongstudio.cafe.feature.openbill.OpenBillSwitch
import id.kongstudio.cafe.feature.openbill.OpenBillSettingScreen
import id.kongstudio.cafe.feature.extrafunds.ExtraFundTables
import id.kongstudio.cafe.feature.addons.AddOnTables
import id.kongstudio.cafe.feature.recipes.RecipeTables
import id.kongstudio.cafe.feature.promotions.PromotionTables
import id.kongstudio.cafe.feature.ordernotes.OrderNoteTables
import id.kongstudio.cafe.feature.visitorcategories.VisitorOptionTables
import id.kongstudio.cafe.feature.openbill.OpenBillRepository
import id.kongstudio.cafe.feature.openbill.OpenBillsScreen
import id.kongstudio.cafe.feature.stationboard.CashierOrder
import id.kongstudio.cafe.feature.admin.ListPage
import id.kongstudio.cafe.feature.stationboard.BoardTables
import id.kongstudio.cafe.feature.devicesetup.map
import id.kongstudio.cafe.feature.periods.BranchPeriodRepository
import id.kongstudio.cafe.feature.periods.BranchPeriodsViewModel
import id.kongstudio.cafe.feature.periods.PeriodTables
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import id.kongstudio.cafe.core.network.ApiConfig
import id.kongstudio.cafe.core.time.BusinessDay
import id.kongstudio.cafe.feature.about.AboutPage
import id.kongstudio.cafe.feature.access.UserAccess
import id.kongstudio.cafe.feature.addons.AddOn
import id.kongstudio.cafe.feature.addons.AddOnPageSize
import id.kongstudio.cafe.feature.addons.AddOnRepository
import id.kongstudio.cafe.feature.addons.AddOnScreen
import id.kongstudio.cafe.feature.addons.KindVariant
import id.kongstudio.cafe.feature.admin.AdminApi
import id.kongstudio.cafe.feature.admin.PagedListViewModel
import id.kongstudio.cafe.feature.userchoice.UserChoiceRepository
import id.kongstudio.cafe.feature.cashier.CashierMenuTables
import id.kongstudio.cafe.feature.cashier.CashierScreen
import id.kongstudio.cafe.feature.cashier.CashierViewModel
import id.kongstudio.cafe.feature.expenses.ExpenseItem
import id.kongstudio.cafe.feature.expenses.ExpensePageSize
import id.kongstudio.cafe.feature.expenses.ExpenseRepository
import id.kongstudio.cafe.feature.expenses.ExpenseScreen
import id.kongstudio.cafe.feature.expenses.ExpenseTables
import id.kongstudio.cafe.feature.extrafunds.ExtraFund
import id.kongstudio.cafe.feature.extrafunds.ExtraFundPageSize
import id.kongstudio.cafe.feature.extrafunds.ExtraFundRepository
import id.kongstudio.cafe.feature.extrafunds.ExtraFundScreen
import id.kongstudio.cafe.feature.menumanage.MenuEntry
import id.kongstudio.cafe.feature.menumanage.MenuDetailOrderTables
import id.kongstudio.cafe.feature.menumanage.MenuManagePageSize
import id.kongstudio.cafe.feature.menumanage.MenuManageRepository
import id.kongstudio.cafe.feature.menumanage.MenuManageScreen
import id.kongstudio.cafe.feature.mysession.MySessionScreen
import id.kongstudio.cafe.feature.mysession.MySessionViewModel
import id.kongstudio.cafe.feature.network.LiveFeed
import id.kongstudio.cafe.feature.ordersync.OfflineScreen
import id.kongstudio.cafe.feature.ordersync.OrderSyncViewModel
import id.kongstudio.cafe.feature.ordernotes.OrderNote
import id.kongstudio.cafe.feature.ordernotes.OrderNotePageSize
import id.kongstudio.cafe.feature.ordernotes.OrderNoteRepository
import id.kongstudio.cafe.feature.ordernotes.OrderNoteScreen

import id.kongstudio.cafe.feature.printer.PrinterScreen
import id.kongstudio.cafe.feature.printer.PrinterViewModel
import id.kongstudio.cafe.feature.printer.ThermalPrinters
import id.kongstudio.cafe.feature.printer.testPageBytes
import id.kongstudio.cafe.feature.ingredientstock.EntryMode
import id.kongstudio.cafe.feature.ingredientstock.IngredientCountScreen
import id.kongstudio.cafe.feature.ingredientstock.IngredientEntryScreen
import id.kongstudio.cafe.feature.ingredientstock.IngredientJourneyViewModel
import id.kongstudio.cafe.feature.ingredientstock.IngredientListScreen
import id.kongstudio.cafe.feature.ingredientstock.IngredientStockRepository
import id.kongstudio.cafe.feature.ingredientstock.RecipeUse
import id.kongstudio.cafe.feature.ingredientstock.RecipeUseTables
import id.kongstudio.cafe.feature.ingredientstock.StockIngredient
import id.kongstudio.cafe.feature.ingredientstock.StockMovement
import id.kongstudio.cafe.feature.ingredientstock.StockPageSize
import id.kongstudio.cafe.feature.ingredientstock.StockPeriodViewModel
import id.kongstudio.cafe.feature.ingredientstock.StockTables
import id.kongstudio.cafe.ui.component.resourcelist.SortKey
import id.kongstudio.cafe.feature.ingredientstock.movementKindsOf
import id.kongstudio.cafe.feature.ingredientstock.OpeningBulkViewModel
import id.kongstudio.cafe.feature.promotions.KindDiscount
import id.kongstudio.cafe.feature.promotions.Promotion
import id.kongstudio.cafe.feature.promotions.PromotionPageSize
import id.kongstudio.cafe.feature.promotions.PromotionRepository
import id.kongstudio.cafe.feature.promotions.PromotionScreen
import id.kongstudio.cafe.feature.resalestock.ResaleCountViewModel
import id.kongstudio.cafe.feature.resalestock.ResalePageSize
import id.kongstudio.cafe.feature.resalestock.ResaleRow
import id.kongstudio.cafe.feature.resalestock.ResaleStockRepository
import id.kongstudio.cafe.feature.resalestock.ResaleStockScreen
import id.kongstudio.cafe.feature.resalestock.ResaleTables
import id.kongstudio.cafe.feature.resalestock.FilterStock
import id.kongstudio.cafe.feature.recipes.RecipeEntry
import id.kongstudio.cafe.feature.recipes.RecipePageSize
import id.kongstudio.cafe.feature.recipes.RecipeRepository
import id.kongstudio.cafe.feature.recipes.RecipeScreen
import id.kongstudio.cafe.feature.sessions.SessionControlViewModel
import id.kongstudio.cafe.feature.sessions.SessionItem
import id.kongstudio.cafe.feature.sessions.SessionPageSize
import id.kongstudio.cafe.feature.sessions.SessionRepository
import id.kongstudio.cafe.feature.stationboard.CashierOrderRepository
import id.kongstudio.cafe.feature.stationboard.CashierOrdersViewModel
import id.kongstudio.cafe.feature.stationboard.OrderHistoryScreen
import id.kongstudio.cafe.feature.stationboard.OrderReprinter
import id.kongstudio.cafe.feature.stationboard.StationBoardRepository
import id.kongstudio.cafe.feature.stationboard.StationBoardScreen
import id.kongstudio.cafe.feature.stationboard.StationBoardViewModel
import id.kongstudio.cafe.feature.stationboard.StationSoundPrefs
import id.kongstudio.cafe.feature.visitorcategories.SectionCategory
import id.kongstudio.cafe.feature.visitorcategories.VisitorOption
import id.kongstudio.cafe.feature.visitorcategories.VisitorOptionPageSize
import id.kongstudio.cafe.feature.visitorcategories.VisitorOptionRepository
import id.kongstudio.cafe.feature.visitorcategories.VisitorOptionScreen
import id.kongstudio.cafe.offline.OfflineStore
import id.kongstudio.cafe.resources.Res

import id.kongstudio.cafe.resources.printer_test_statement
import io.ktor.client.HttpClient
import org.jetbrains.compose.resources.stringResource


/** Bahan yang dipakai semua layar tujuan: klien, token karyawan, dan aksi saat token ditolak. */
internal class OperationalDeps(
    val client: HttpClient,
    val userToken: String,
    deviceToken: String,
    val printers: ThermalPrinters,
    val onUserExpired: () -> Unit,
    val store: OfflineStore,
) {
    /** Saklar Open Bill tablet ini, satu untuk semua layar. */
    val openBill = OpenBillSwitch(store)

    /** Kunci ViewModel layar: berganti bila karyawan atau token tablet berganti, supaya tidak ada yang memegang token lama. */
    val key = "$userToken-$deviceToken"
    val v2Api = AdminApi(client, ApiConfig.V2_BASE_URL, userToken, deviceToken)
    val live = LiveFeed(client, ApiConfig.V2_BASE_URL, userToken, onUserExpired)
}

/** Menampilkan layar untuk satu tujuan; ViewModel dibuat saat tujuannya pertama dibuka. */
private const val OpenBillPageSize = 100

@Composable
internal fun OperationalHost(
    destination: OperationalDestination,
    deps: OperationalDeps,
    access: UserAccess,
    cashier: CashierViewModel,
    sync: OrderSyncViewModel,
    session: SessionControlViewModel,
    canControlSession: Boolean,
    focusHandover: Boolean,
    onFocusHandled: () -> Unit,
    onSelectDestination: (OperationalDestination) -> Unit,
    modifier: Modifier = Modifier,
) {
    val key = deps.key
    val userChoices = remember(deps.v2Api) { UserChoiceRepository(deps.v2Api) }
    // Dibuat sebelum layar mana pun supaya periode sudah terbaca saat daftar bertanggal pertama dibuka.
    val periods = viewModel(key = "branch-periods-$key") {
        BranchPeriodsViewModel(BranchPeriodRepository(deps.v2Api), deps.live.of(PeriodTables), deps.onUserExpired)
    }
    when (destination) {
        OperationalDestination.Printer -> {
            val statement = stringResource(Res.string.printer_test_statement)
            val printer = viewModel(key = "printer-$key") {
                PrinterViewModel(
                    printers = deps.printers,
                    plan = cashier.printPlan,
                    planFailure = cashier.printPlanFailure,
                    onRetryPlan = cashier::reloadPrintPlan,
                    testPage = { name, paper, logo -> testPageBytes(name, paper, statement, logo) },
                )
            }
            PrinterScreen(viewModel = printer, modifier = modifier)
        }

        OperationalDestination.OpenBillSetting -> {
            val repository = remember(deps.v2Api) { OpenBillRepository(deps.v2Api) }
            OpenBillSettingScreen(title = stringResource(OperationalDestination.OpenBillSetting.label), switch = deps.openBill, repository = repository, modifier = modifier)
        }

        OperationalDestination.Offline -> {
            val cashierState by cashier.state.collectAsState()
            OfflineScreen(viewModel = sync, catalog = cashierState.items, methods = cashierState.methods, modifier = modifier)
        }

        OperationalDestination.Info -> AboutPage(modifier = modifier, title = stringResource(OperationalDestination.Info.label))

        OperationalDestination.Cashier -> CashierScreen(
            viewModel = cashier,
            modifier = modifier,
            openBillEnabled = deps.openBill.enabled.collectAsState().value,
            onOpenSession = { session.showOpen() }.takeIf { canControlSession },
        )

        OperationalDestination.MySession -> {
            val repository = remember(deps.v2Api) { SessionRepository(deps.v2Api) }
            val mine = viewModel(key = "my-session-$key") {
                MySessionViewModel(repository = repository, onUnauthorized = deps.onUserExpired)
            }
            val history = viewModel(key = "my-session-history-$key") {
                PagedListViewModel<SessionItem>(
                    pageSize = SessionPageSize,
                    loader = { request -> repository.list(request) },
                    onUnauthorized = deps.onUserExpired,
                )
            }
            val sessionState by session.state.collectAsState()
            MySessionScreen(
                viewModel = mine,
                history = history,
                activeId = sessionState.active?.id,
                canControl = canControlSession,
                onOpen = session::showOpen,
                onClose = session::showClose,
                modifier = modifier,
            )
        }

        OperationalDestination.Stations -> {
            val repository = remember(deps.v2Api) { StationBoardRepository(deps.v2Api) }
            // Stasiun diambil dari yang ditetapkan untuk tablet ini di tab Perangkat halaman Cabang, bukan dari peran akun.
            val board = viewModel(key = "stations-$key") {
                StationBoardViewModel(
                    repository = repository,
                    live = deps.live,
                    soundPrefs = StationSoundPrefs(deps.store),
                    onUnauthorized = deps.onUserExpired,
                    printers = deps.printers,
                    printPlan = cashier.printPlan,
                )
            }
            val cashierOrders = rememberCashierOrders(deps, cashier, session, repository)
            StationBoardScreen(
                viewModel = board,
                access = access,
                cashierOrders = cashierOrders,
                focusHandover = focusHandover,
                onFocusHandled = onFocusHandled,
                modifier = modifier,
            )
        }

        OperationalDestination.OrderHistory -> {
            val board = remember(deps.v2Api) { StationBoardRepository(deps.v2Api) }
            OrderHistoryScreen(
                orders = rememberCashierOrders(deps, cashier, session, board),
                access = access,
                title = stringResource(OperationalDestination.OrderHistory.label),
                modifier = modifier,
            )
        }

        OperationalDestination.OpenBills -> {
            val repository = remember(deps.v2Api) { OpenBillRepository(deps.v2Api) }
            val list = viewModel(key = "open-bills-$key") {
                PagedListViewModel<CashierOrder>(
                    pageSize = OpenBillPageSize,
                    loader = { request ->
                        val term = request.query.trim().lowercase()
                        repository.bills().map { all ->
                            val found = all.filter { term.isEmpty() || (it.receipt.orEmpty() + " " + it.tableNo.orEmpty()).lowercase().contains(term) }
                            ListPage(found.take(OpenBillPageSize), found.size)
                        }
                    },
                    onUnauthorized = deps.onUserExpired,
                    changes = deps.live.of(BoardTables),
                )
            }
            OpenBillsScreen(
                title = stringResource(OperationalDestination.OpenBills.label),
                viewModel = list,
                repository = repository,
                cashier = cashier,
                onAddMenu = { bill ->
                    cashier.startAdding(bill)
                    onSelectDestination(OperationalDestination.Cashier)
                },
                modifier = modifier,
            )
        }

        OperationalDestination.ExtraFunds -> {
            val repository = remember(deps.v2Api) { ExtraFundRepository(deps.v2Api) }
            val list = viewModel(key = "extrafunds-$key") {
                val today = BusinessDay.today()
                PagedListViewModel<ExtraFund>(
                    pageSize = ExtraFundPageSize,
                    loader = repository::list,
                    onUnauthorized = deps.onUserExpired,
                    initialSort = "-recorded_at",
                    initialParams = periods.initialParams(today),
                    changes = deps.live.of(ExtraFundTables),
                )
            }
            ExtraFundScreen(viewModel = list, repository = repository, userChoices = userChoices, periods = periods, modifier = modifier)
        }

        OperationalDestination.Expenses -> {
            val repository = remember(deps.v2Api) { ExpenseRepository(deps.v2Api) }
            val list = viewModel(key = "expenses-$key") {
                val today = BusinessDay.today()
                PagedListViewModel<ExpenseItem>(
                    pageSize = ExpensePageSize,
                    loader = repository::list,
                    onUnauthorized = deps.onUserExpired,
                    initialSort = "-created_at",
                    initialParams = periods.initialParams(today),
                    changes = deps.live.of(ExpenseTables),
                )
            }
            ExpenseScreen(viewModel = list, repository = repository, access = access, userChoices = userChoices, periods = periods, modifier = modifier)
        }

        OperationalDestination.IngredientList -> {
            val repository = remember(deps.v2Api) { IngredientStockRepository(deps.v2Api) }
            val list = viewModel(key = "ingredient-list-$key") {
                PagedListViewModel<StockIngredient>(
                    pageSize = StockPageSize,
                    loader = repository::ingredients,
                    onUnauthorized = deps.onUserExpired,
                    initialSort = SortKey.NameAsc,
                    changes = deps.live.of(StockTables),
                )
            }
            val recipes = remember(deps.v2Api) { RecipeRepository(deps.v2Api) }
            IngredientListScreen(
                viewModel = list,
                recipes = recipes,
                uses = { ingredientId ->
                    viewModel(key = "ingredient-uses-$key-$ingredientId") {
                        PagedListViewModel<RecipeUse>(
                            pageSize = StockPageSize,
                            loader = { request -> repository.recipeUses(ingredientId, request) },
                            onUnauthorized = deps.onUserExpired,
                            changes = deps.live.of(RecipeUseTables),
                        )
                    }
                },
                access = access,
                modifier = modifier,
            )
        }

        OperationalDestination.IngredientReceipts, OperationalDestination.IngredientWaste -> {
            val repository = remember(deps.v2Api) { IngredientStockRepository(deps.v2Api) }
            val mode = if (destination == OperationalDestination.IngredientReceipts) EntryMode.Receipts else EntryMode.WasteAndTrial
            val list = viewModel(key = "ingredient-entries-${mode.name}-$key") {
                val today = BusinessDay.today()
                PagedListViewModel<StockMovement>(
                    pageSize = StockPageSize,
                    loader = { request -> repository.movements(movementKindsOf(mode, request.filter), request) },
                    onUnauthorized = deps.onUserExpired,
                    initialParams = periods.initialParams(today),
                    initialSort = SortKey.Newest,
                    changes = deps.live.of(StockTables),
                )
            }
            IngredientEntryScreen(mode = mode, viewModel = list, repository = repository, userChoices = userChoices, access = access, periods = periods, modifier = modifier)
        }

        OperationalDestination.IngredientCounts -> {
            val repository = remember(deps.v2Api) { IngredientStockRepository(deps.v2Api) }
            val list = viewModel(key = "ingredient-count-list-$key") {
                PagedListViewModel<StockIngredient>(
                    pageSize = StockPageSize,
                    loader = repository::ingredients,
                    onUnauthorized = deps.onUserExpired,
                    initialSort = SortKey.NameAsc,
                    changes = deps.live.of(StockTables),
                )
            }
            val period = viewModel(key = "ingredient-period-$key") {
                StockPeriodViewModel(repository = repository, onUnauthorized = deps.onUserExpired, changes = deps.live.of(StockTables))
            }
            IngredientCountScreen(
                list = list,
                period = period,
                journey = { ingredientId ->
                    viewModel(key = "ingredient-journey-$key-$ingredientId") {
                        IngredientJourneyViewModel(
                            ingredientId = ingredientId,
                            repository = repository,
                            onUnauthorized = deps.onUserExpired,
                            changes = deps.live.of(StockTables),
                        )
                    }
                },
                history = { ingredientId ->
                    viewModel(key = "ingredient-history-$key-$ingredientId") {
                        PagedListViewModel<StockMovement>(
                            pageSize = StockPageSize,
                            loader = { request -> repository.ingredientMovements(ingredientId, request) },
                            onUnauthorized = deps.onUserExpired,
                            changes = deps.live.of(StockTables),
                        )
                    }
                },
                bulk = {
                    viewModel(key = "ingredient-opening-bulk-$key") {
                        OpeningBulkViewModel(repository = repository, onUnauthorized = deps.onUserExpired)
                    }
                },
                repository = repository,
                userChoices = userChoices,
                access = access,
                modifier = modifier,
            )
        }

        OperationalDestination.ResaleStock -> {
            val repository = remember(deps.v2Api) { ResaleStockRepository(deps.v2Api) }
            val list = viewModel(key = "resale-stock-$key") {
                val today = BusinessDay.today()
                PagedListViewModel<ResaleRow>(
                    pageSize = ResalePageSize,
                    loader = repository::rows,
                    onUnauthorized = deps.onUserExpired,
                    initialFilter = FilterStock,
                    initialParams = periods.initialParams(today),
                    initialSort = SortKey.NameAsc,
                    changes = deps.live.of(ResaleTables),
                )
            }
            val count = viewModel(key = "resale-count-$key") {
                ResaleCountViewModel(repository = repository, onUnauthorized = deps.onUserExpired, onSaved = list::reload)
            }
            ResaleStockScreen(viewModel = list, repository = repository, count = count, userChoices = userChoices, access = access, periods = periods, modifier = modifier)
        }

        OperationalDestination.MenuManage -> {
            val repository = remember(deps.v2Api) { MenuManageRepository(deps.v2Api) }
            val list = viewModel(key = "menu-manage-$key") {
                PagedListViewModel<MenuEntry>(
                    pageSize = MenuManagePageSize,
                    loader = repository::list,
                    onUnauthorized = deps.onUserExpired,
                    changes = deps.live.of(CashierMenuTables),
                )
            }
            // Rincian ikut dimuat ulang saat pesanan berubah, karena stok bahan dan jumlah terjual bergantung padanya.
            val detailChanges = remember(deps.live) { deps.live.of(CashierMenuTables + MenuDetailOrderTables) }
            MenuManageScreen(viewModel = list, repository = repository, access = access, detailChanges = detailChanges, modifier = modifier)
        }

        OperationalDestination.AddOns -> {
            val repository = remember(deps.v2Api) { AddOnRepository(deps.v2Api) }
            val list = viewModel(key = "addons-$key") {
                PagedListViewModel<AddOn>(
                    pageSize = AddOnPageSize,
                    loader = repository::list,
                    onUnauthorized = deps.onUserExpired,
                    initialFilter = KindVariant,
                    changes = deps.live.of(AddOnTables),
                )
            }
            AddOnScreen(viewModel = list, repository = repository, access = access, modifier = modifier)
        }

        OperationalDestination.Recipes -> {
            val repository = remember(deps.v2Api) { RecipeRepository(deps.v2Api) }
            val list = viewModel(key = "recipes-$key") {
                PagedListViewModel<RecipeEntry>(
                    pageSize = RecipePageSize,
                    loader = repository::list,
                    onUnauthorized = deps.onUserExpired,
                    changes = deps.live.of(RecipeTables),
                )
            }
            RecipeScreen(viewModel = list, repository = repository, access = access, modifier = modifier)
        }

        OperationalDestination.Promotions -> {
            val repository = remember(deps.v2Api) { PromotionRepository(deps.v2Api) }
            val list = viewModel(key = "promotions-$key") {
                PagedListViewModel<Promotion>(
                    pageSize = PromotionPageSize,
                    loader = repository::list,
                    onUnauthorized = deps.onUserExpired,
                    initialFilter = KindDiscount,
                    changes = deps.live.of(PromotionTables),
                )
            }
            PromotionScreen(viewModel = list, repository = repository, access = access, modifier = modifier)
        }

        OperationalDestination.OrderNotes -> {
            val repository = remember(deps.v2Api) { OrderNoteRepository(deps.v2Api) }
            val list = viewModel(key = "order-notes-$key") {
                PagedListViewModel<OrderNote>(
                    pageSize = OrderNotePageSize,
                    loader = repository::list,
                    onUnauthorized = deps.onUserExpired,
                    initialSort = SortKey.NameAsc,
                    changes = deps.live.of(OrderNoteTables),
                )
            }
            OrderNoteScreen(viewModel = list, repository = repository, userChoices = userChoices, access = access, modifier = modifier)
        }

        OperationalDestination.VisitorCategories -> {
            val repository = remember(deps.v2Api) { VisitorOptionRepository(deps.v2Api) }
            val list = viewModel(key = "visitor-options-$key") {
                PagedListViewModel<VisitorOption>(
                    pageSize = VisitorOptionPageSize,
                    loader = repository::list,
                    onUnauthorized = deps.onUserExpired,
                    initialFilter = SectionCategory,
                    changes = deps.live.of(VisitorOptionTables),
                )
            }
            VisitorOptionScreen(viewModel = list, repository = repository, access = access, modifier = modifier)
        }
    }
}

/** Daftar pesanan sesi kasir yang berjalan, dipakai bersama tab Kasir di Papan Stasiun dan Riwayat Pesanan; null selama sesi belum dibuka. */
@Composable
private fun rememberCashierOrders(
    deps: OperationalDeps,
    cashier: CashierViewModel,
    session: SessionControlViewModel,
    board: StationBoardRepository,
): CashierOrdersViewModel? {
    val sessionState by session.state.collectAsState()
    val sessionId = sessionState.active?.id ?: return null
    val orderRepository = remember(deps.v2Api) { CashierOrderRepository(deps.v2Api) }
    return viewModel(key = "cashier-orders-${deps.key}-$sessionId") {
        CashierOrdersViewModel(
            sessionId = sessionId,
            repository = orderRepository,
            board = board,
            live = deps.live,
            reprinter = OrderReprinter(
                categoryOf = cashier::categoryOfMenu,
                slots = cashier::reprintSlots,
                print = cashier::reprint,
                plan = { cashier.printPlan.value },
            ),
            onUnauthorized = deps.onUserExpired,
        )
    }
}
