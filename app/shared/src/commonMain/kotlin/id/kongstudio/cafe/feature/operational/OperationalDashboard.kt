package id.kongstudio.cafe.feature.operational

import androidx.compose.runtime.mutableIntStateOf
import id.kongstudio.cafe.feature.stationboard.BoardTables
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.core.network.ApiConfig
import id.kongstudio.cafe.feature.access.Permission
import id.kongstudio.cafe.feature.access.UserAccess
import id.kongstudio.cafe.feature.access.UserAccessRepository
import id.kongstudio.cafe.feature.cashier.CashierMenuTables
import id.kongstudio.cafe.feature.cashier.CartDraftStore
import id.kongstudio.cafe.feature.openbill.OpenBillRepository
import id.kongstudio.cafe.feature.cashier.CashierReferenceTables
import id.kongstudio.cafe.feature.cashier.CashierRepository
import id.kongstudio.cafe.feature.cashier.CashierViewModel
import id.kongstudio.cafe.feature.cashier.activeCategory
import id.kongstudio.cafe.feature.cashier.categoryLabel
import id.kongstudio.cafe.feature.cashier.categoryTabs
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.feature.network.NetworkMonitor
import id.kongstudio.cafe.feature.operationalmenu.OperationalMenuScreen
import id.kongstudio.cafe.feature.operationalmenu.menuTabLabel
import id.kongstudio.cafe.feature.ordersync.OrderSyncStatus
import id.kongstudio.cafe.feature.ordersync.OrderSyncViewModel
import id.kongstudio.cafe.feature.ordersync.OrderSyncer
import id.kongstudio.cafe.feature.printer.PrintPlanTables
import id.kongstudio.cafe.feature.printer.PrinterReportRepository
import id.kongstudio.cafe.feature.printer.PrinterReporter
import id.kongstudio.cafe.feature.printer.TabletMode
import id.kongstudio.cafe.feature.printer.ThermalPrinters
import id.kongstudio.cafe.feature.release.ReleaseRoute
import id.kongstudio.cafe.feature.sessions.CloseSessionSheet
import id.kongstudio.cafe.feature.sessions.OpenSessionSheet
import id.kongstudio.cafe.feature.sessions.SessionControlRepository
import id.kongstudio.cafe.feature.sessions.SessionControlViewModel
import id.kongstudio.cafe.feature.sessions.SessionLeftBehindDialog
import id.kongstudio.cafe.feature.sessions.SessionSheet
import id.kongstudio.cafe.feature.sessions.SignOutSheet
import id.kongstudio.cafe.offline.OfflineStore
import id.kongstudio.cafe.offline.QueueCounts
import id.kongstudio.cafe.offline.userIdOf
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.brand_logo
import id.kongstudio.cafe.resources.session_card_cash
import id.kongstudio.cafe.resources.session_card_none
import id.kongstudio.cafe.resources.session_card_unknown
import id.kongstudio.cafe.resources.shell_logo_description
import id.kongstudio.cafe.resources.shell_rail_collapse
import id.kongstudio.cafe.resources.shell_rail_expand
import id.kongstudio.cafe.resources.user_sign_out
import id.kongstudio.cafe.resources.user_sign_out_close_session_first
import id.kongstudio.cafe.resources.user_sign_out_needs_network
import id.kongstudio.cafe.ui.component.appshell.AppShell
import id.kongstudio.cafe.ui.component.bottombar.AppBottomBar
import id.kongstudio.cafe.ui.component.bottombar.BottomBarItem
import id.kongstudio.cafe.ui.component.sidebargroup.SidebarGroup
import id.kongstudio.cafe.ui.component.sidebarheader.SidebarHeader
import id.kongstudio.cafe.ui.component.sidebaritem.SidebarItem
import id.kongstudio.cafe.ui.component.sidebarsessionpanel.SidebarSessionPanel
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import io.ktor.client.HttpClient
import kotlinx.coroutines.flow.flowOf
import org.jetbrains.compose.resources.painterResource
import org.jetbrains.compose.resources.stringResource

private const val GroupSeparator = ","

// Tabel yang menentukan menu dan izin staf: peran milik staf dan isi izin perannya.
private val UserAccessTables = setOf("users", "roles")

/** Kerangka perangkat operasional: rail berkelompok di tablet dan bilah bawah di layar sempit, dengan tujuan mengikuti izin karyawan. */
@Composable
internal fun OperationalDashboard(
    deviceName: String,
    userName: String?,
    userToken: String,
    deviceToken: String,
    client: HttpClient,
    store: OfflineStore,
    printers: ThermalPrinters,
    network: NetworkMonitor,
    onUserExpired: () -> Unit,
    onSignOut: () -> Unit,
    onSessionOpen: (Boolean) -> Unit,
    modifier: Modifier = Modifier,
) {
    val online by network.online.collectAsState()
    val deps = remember(userToken, deviceToken) { OperationalDeps(client, userToken, deviceToken, printers, onUserExpired, store) }
    LaunchedEffect(deps) { deps.live.run(network.online) }
    LaunchedEffect(deps) { PrinterReporter(PrinterReportRepository(deps.v2Api), printers).run() }
    // Kunci memuat token karyawan dan tablet: karyawan berbeda atau token tablet baru mendapat keranjang dan katalog yang baru.
    val cashier = viewModel(key = "cashier-${deps.key}") {
        CashierViewModel(
            repository = CashierRepository(client, ApiConfig.V2_BASE_URL, userToken, deviceToken, store),
            printers = printers,
            cashierName = userName.orEmpty(),
            onUnauthorized = onUserExpired,
            draft = userIdOf(userToken)?.let { CartDraftStore(store, it) },
            bills = OpenBillRepository(deps.v2Api),
            printPlanChanges = deps.live.of(PrintPlanTables),
            menuChanges = deps.live.of(CashierMenuTables),
            referenceChanges = deps.live.of(CashierReferenceTables),
        )
    }
    val cashierState by cashier.state.collectAsState()
    val session = viewModel(key = "session-${deps.key}") {
        SessionControlViewModel(
            repository = SessionControlRepository(client, ApiConfig.V2_BASE_URL, userToken, deviceToken),
            queue = userIdOf(userToken)?.let(store::countsFor) ?: flowOf(QueueCounts()),
            connected = deps.live.connected,
            onChanged = cashier::refreshShift,
            onSignOut = onSignOut,
            onUnauthorized = onUserExpired,
        )
    }
    val sessionState by session.state.collectAsState()
    // Pembaruan wajib ditunda hanya selama sesi kasir di tablet ini berjalan; keluar dari dasbor berarti tidak ada sesi yang dipegang.
    val sessionOpen = sessionState.active != null
    LaunchedEffect(sessionOpen) { onSessionOpen(sessionOpen) }
    DisposableEffect(Unit) { onDispose { onSessionOpen(false) } }
    val sync = viewModel(key = "sync-${deps.key}") {
        OrderSyncViewModel(
            syncer = OrderSyncer(client, ApiConfig.V2_BASE_URL, userToken, deviceToken, store),
            store = store,
            live = deps.live,
            ownerId = userIdOf(userToken),
            onLoginRequired = onUserExpired,
        )
    }

    var access by remember(deps) { mutableStateOf<UserAccess?>(null) }
    val accessChanges = remember(deps) { deps.live.of(UserAccessTables) }
    // Peran atau izin yang diubah di web berlaku di menu tablet tanpa masuk ulang; kegagalan sesaat mempertahankan akses terakhir.
    LaunchedEffect(deps) {
        val repository = UserAccessRepository(deps.v2Api, store, userToken)
        suspend fun reload() {
            when (val result = repository.load()) {
                is DeviceResult.Ok -> access = result.value
                is DeviceResult.Failed -> if (result.failure == AppFailure.Unauthorized) onUserExpired()
            }
        }
        reload()
        accessChanges.collect { reload() }
    }

    val canControlSession = access?.allows(Permission.SessionOpen) == true
    val printPlan by cashier.printPlan.collectAsState()
    val tabletMode = printPlan?.mode
    val openBillOn by deps.openBill.enabled.collectAsState()
    var unpaidBills by remember { mutableIntStateOf(0) }
    LaunchedEffect(deps) { deps.openBill.load() }
    // Open Bill mati tidak boleh mengunci bill yang masih ada, jadi menunya tetap muncul selama ada bill; dimuat ulang lewat sinyal live, tanpa polling.
    LaunchedEffect(deps, openBillOn, tabletMode) {
        if (openBillOn || tabletMode != TabletMode.Cashier) {
            unpaidBills = 0
            return@LaunchedEffect
        }
        val repository = OpenBillRepository(deps.v2Api)
        suspend fun reload() {
            (repository.bills() as? DeviceResult.Ok)?.let { unpaidBills = it.value.size }
        }
        reload()
        deps.live.of(BoardTables).collect { reload() }
    }
    val destinations = OperationalDestination.entries.filter { it.visibleTo(access) && it.fits(tabletMode, openBillVisible = openBillOn || unpaidBills > 0) }
    var destinationName by rememberSaveable { mutableStateOf(OperationalDestination.Cashier.name) }
    var menuOpen by rememberSaveable { mutableStateOf(false) }
    var expandedRaw by rememberSaveable {
        mutableStateOf(OperationalGroup.entries.joinToString(GroupSeparator) { it.name })
    }

    // Tujuan yang tidak dikenal atau tidak diizinkan peran jatuh ke tujuan pertama yang boleh dibuka.
    val destination = OperationalDestination.entries.firstOrNull { it.name == destinationName }
        ?.takeIf { it in destinations } ?: destinations.firstOrNull() ?: OperationalDestination.Cashier
    val expanded = expandedRaw.split(GroupSeparator).toSet()
    val primaryTabs = listOf(OperationalDestination.Cashier)
    val hasMenu = destinations.any { it !in primaryTabs }
    val select = { target: OperationalDestination ->
        destinationName = target.name
        menuOpen = false
    }
    // Tangani sekarang dari pengingat Tertinggal membuka tab Kasir di Papan Stasiun.
    var focusHandover by remember { mutableStateOf(false) }
    val menuLabel = menuTabLabel()
    // Keluar hanya tampil setelah sesi tertutup (ditutup di halaman Sesi Kasir Saya); status yang belum terbaca juga ditahan.
    val canSignOut = !canControlSession || (sessionState.known && sessionState.active == null)
    val signOutLabel = stringResource(Res.string.user_sign_out)
    // Keluar yang ditahan selalu diberi alasan: sesi masih terbuka, atau status sesi belum terbaca.
    val closeFirstHint = stringResource(Res.string.user_sign_out_close_session_first)
    val needsNetworkHint = stringResource(Res.string.user_sign_out_needs_network)
    val signOutHint = when {
        !canControlSession -> null
        sessionState.active != null -> closeFirstHint
        !sessionState.known -> needsNetworkHint
        else -> null
    }
    val signOut = { session.signOut(canHoldSession = canControlSession) }
    val reviewRejected = {
        session.dismiss()
        sync.openReview()
    }
    LaunchedEffect(sessionState.sheet) {
        if (sessionState.sheet == SessionSheet.Close || sessionState.sheet == SessionSheet.SignOut) sync.syncNow()
    }

    AppShell(
        modifier = modifier,
        slidingRail = true,
        hideRailDescription = stringResource(Res.string.shell_rail_collapse),
        showRailDescription = stringResource(Res.string.shell_rail_expand),
        bottomBar = {
            AppBottomBar(
                items = buildList {
                    primaryTabs.filter { it in destinations }.forEach { tab ->
                        add(
                            BottomBarItem(
                                label = stringResource(tab.label),
                                icon = tab.icon,
                                selected = destination == tab && !menuOpen,
                                onClick = { select(tab) },
                            ),
                        )
                    }
                    if (hasMenu) {
                        add(
                            BottomBarItem(
                                label = menuLabel,
                                icon = AppIcons.More,
                                selected = menuOpen || destination !in primaryTabs,
                                onClick = { menuOpen = true },
                            ),
                        )
                    }
                },
            )
        },
        rail = { collapsed, _ ->
            SidebarHeader(
                logo = painterResource(Res.drawable.brand_logo),
                logoDescription = stringResource(Res.string.shell_logo_description),
                title = deviceName,
                subtitle = userName.orEmpty(),
                collapsed = collapsed,
                onToggleCollapsed = null,
                collapseDescription = stringResource(Res.string.shell_rail_collapse),
                expandDescription = stringResource(Res.string.shell_rail_expand),
            )
            val toggleGroup = { group: OperationalGroup ->
                expandedRaw = if (group.name in expanded) {
                    (expanded - group.name).joinToString(GroupSeparator)
                } else {
                    (expanded + group.name).joinToString(GroupSeparator)
                }
            }
            val sidebarItem: @Composable (OperationalDestination) -> Unit = { item ->
                    SidebarItem(
                        label = stringResource(item.label),
                        icon = item.icon,
                        selected = item == destination,
                        onClick = { select(item) },
                    )
                    if (item == OperationalDestination.Cashier && destination == item && !menuOpen && !collapsed) {
                        val active = cashierState.activeCategory
                        cashierState.categoryTabs().forEach { tab ->
                            SidebarItem(
                                label = categoryLabel(tab),
                                icon = null,
                                selected = tab == active,
                                onClick = { cashier.selectCategory(tab) },
                                modifier = Modifier.padding(start = AppTheme.spacing.lg),
                            )
                        }
                    }
                }

            Column(modifier = Modifier.weight(1f).verticalScroll(rememberScrollState())) {
                OperationalGroup.entries.filter { it != OperationalGroup.Session }.forEach { group ->
                    val items = destinations.filter { it.group == group }
                    if (items.isEmpty()) return@forEach
                    // Kasir tidak punya judul grup: namanya sama dengan item Kasir di dalamnya.
                    if (group == OperationalGroup.Cashier) {
                        Column(verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.xs)) {
                            items.forEach { sidebarItem(it) }
                        }
                        return@forEach
                    }
                    SidebarGroup(
                        label = stringResource(group.label),
                        icon = group.icon,
                        expanded = group.name in expanded,
                        highlighted = destination.group == group,
                        onToggle = { toggleGroup(group) },
                    ) {
                        items.forEach { sidebarItem(it) }
                    }
                }
            }
            // Sesi kasir bukan menu biasa: satu panel di dasar yang menunjukkan statusnya; buka dan tutup ada di halaman sesi.
            if (OperationalDestination.MySession in destinations) {
                val active = sessionState.active
                SidebarSessionPanel(
                    title = stringResource(OperationalDestination.MySession.label),
                    // Status yang belum terbaca (dibuka saat offline) tidak boleh tampil sebagai sesi belum dibuka.
                    status = when {
                        active != null -> stringResource(Res.string.session_card_cash, formatRupiah(active.openingCash))
                        !sessionState.known -> stringResource(Res.string.session_card_unknown)
                        else -> stringResource(Res.string.session_card_none)
                    },
                    selected = destination == OperationalDestination.MySession && !menuOpen,
                    collapsed = collapsed,
                    onOpenPage = { select(OperationalDestination.MySession) },
                )
            }
            if (!canSignOut && signOutHint != null && !collapsed) {
                AppText(
                    text = signOutHint,
                    role = TextRole.Caption,
                    color = AppTheme.colors.onPrimaryMuted,
                    modifier = Modifier.padding(horizontal = AppTheme.spacing.md),
                )
            }
            if (canSignOut) {
                SidebarItem(
                    label = signOutLabel,
                    icon = AppIcons.Logout,
                    selected = false,
                    onClick = signOut,
                    collapsed = collapsed,
                )
            }
        },
    ) {
        Column(modifier = Modifier.fillMaxSize()) {
            OrderSyncStatus(viewModel = sync)
            Box(modifier = Modifier.weight(1f).fillMaxWidth()) {
                if (menuOpen) {
                    OperationalMenuScreen(
                        destinations = destinations,
                        onSelect = select,
                        signOutLabel = signOutLabel,
                        onSignOut = signOut.takeIf { canSignOut },
                    )
                } else {
                    OperationalHost(
                        destination = destination,
                        deps = deps,
                        access = access ?: UserAccess("", "", emptySet()),
                        cashier = cashier,
                        sync = sync,
                        session = session,
                        canControlSession = canControlSession,
                        focusHandover = focusHandover,
                        onFocusHandled = { focusHandover = false },
                        onSelectDestination = select,
                        modifier = Modifier.fillMaxSize(),
                    )
                }
            }
        }
    }

    when (sessionState.sheet) {
        SessionSheet.Open -> OpenSessionSheet(
            known = sessionState.known,
            submitting = sessionState.submitting,
            failure = sessionState.failure,
            onSubmit = session::submitOpen,
            onDismiss = session::dismiss,
        )
        SessionSheet.Close -> CloseSessionSheet(
            known = sessionState.known,
            recap = sessionState.recap,
            queue = sessionState.queue,
            online = online,
            signsOut = sessionState.signOutAfterClose,
            submitting = sessionState.submitting,
            failure = sessionState.failure,
            onReview = reviewRejected,
            onSubmit = session::submitClose,
            onDismiss = session::dismiss,
        )
        SessionSheet.SignOut -> SignOutSheet(
            known = sessionState.known || !canControlSession,
            queue = sessionState.queue,
            online = online,
            onReview = reviewRejected,
            onDismiss = session::dismiss,
        )
        SessionSheet.None -> ReleaseRoute(api = deps.v2Api, userToken = userToken, onUnauthorized = onUserExpired)
    }
    if (sessionState.sheet == SessionSheet.None && sessionState.leftBehind.isNotEmpty()) {
        SessionLeftBehindDialog(
            orders = sessionState.leftBehind,
            onNow = {
                session.dismissLeftBehind()
                if (tabletMode == TabletMode.Cashier) {
                    select(OperationalDestination.OrderHistory)
                } else {
                    focusHandover = true
                    select(OperationalDestination.Stations)
                }
            },
            onLater = session::dismissLeftBehind,
        )
    }
}
