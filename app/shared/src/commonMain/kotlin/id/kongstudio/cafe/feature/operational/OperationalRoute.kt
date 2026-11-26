package id.kongstudio.cafe.feature.operational

import id.kongstudio.cafe.feature.demo.DemoBanner
import id.kongstudio.cafe.feature.demo.DemoMode
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.statusBars
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import id.kongstudio.cafe.core.network.ApiConfig
import id.kongstudio.cafe.feature.devicesetup.DeviceCodeSheet
import id.kongstudio.cafe.feature.devicesetup.DeviceCredential
import id.kongstudio.cafe.feature.devicesetup.DeviceModeStore
import id.kongstudio.cafe.feature.printer.ThermalPrinters
import id.kongstudio.cafe.offline.OfflineStore
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.device_release_action
import id.kongstudio.cafe.resources.device_release_description
import id.kongstudio.cafe.resources.device_release_invalid
import id.kongstudio.cafe.resources.device_release_title
import id.kongstudio.cafe.resources.operational_farewell_messages
import id.kongstudio.cafe.resources.operational_welcome_messages
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import id.kongstudio.cafe.feature.network.NetworkMonitor
import io.ktor.client.HttpClient
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import org.jetbrains.compose.resources.stringResource

private const val WelcomeHoldMillis = 2_500L

/** Halaman tablet operasional: QR sampai ada karyawan memindai lalu dashboard, dilepas dengan kode perangkat atau otomatis bila server mencabutnya. */
@Composable
internal fun OperationalRoute(
    credential: DeviceCredential,
    client: HttpClient,
    store: DeviceModeStore,
    offlineStore: OfflineStore,
    printers: ThermalPrinters,
    network: NetworkMonitor,
    revoke: (String) -> Unit,
    onReleased: () -> Unit,
    onUserExpired: () -> Unit,
    onSessionOpen: (Boolean) -> Unit,
    demo: DemoMode,
    modifier: Modifier = Modifier,
) {
    val scope = rememberCoroutineScope()
    // Naik tiap karyawan dilepas, supaya alur QR dimulai ulang dengan ViewModel baru.
    var epoch by rememberSaveable { mutableIntStateOf(0) }
    // Diset saat karyawan dilepas, karena credential baru menyusul setelah penyimpanan ditulis dan tautan lama tidak boleh dilanjutkan.
    var userReleased by rememberSaveable { mutableStateOf(false) }
    val alreadyLinked = credential.linked && credential.userToken != null && !userReleased
    // Token karyawan terbaru, agar perangkat yang dicabut server juga mencabut sesi karyawannya.
    var linkedToken by remember(credential.id) { mutableStateOf(credential.userToken) }
    val viewModel = viewModel(key = "operational-${credential.id}-${credential.token}-$epoch") {
        OperationalViewModel(
            client = client,
            baseUrl = ApiConfig.V2_BASE_URL,
            deviceToken = credential.token,
            onRevoked = {
                linkedToken?.let(revoke)
                onReleased()
            },
            onLinked = { name, token ->
                linkedToken = token
                scope.launch { store.markLinked(name, token) }
            },
            alreadyLinked = alreadyLinked,
        )
    }
    val state by viewModel.state.collectAsState()
    val userToken = state.userToken ?: credential.userToken
    var releasing by rememberSaveable { mutableStateOf(false) }
    var invalid by rememberSaveable { mutableStateOf(false) }
    val openMenu = {
        invalid = false
        releasing = true
    }

    // Sambutan hanya untuk scan yang baru terjadi, bukan saat app dibuka ulang.
    var welcomed by rememberSaveable { mutableStateOf(false) }
    val welcoming = state.connected && !alreadyLinked && !welcomed
    LaunchedEffect(welcoming) {
        if (welcoming) {
            delay(WelcomeHoldMillis)
            welcomed = true
        }
    }

    // Salam keluar hanya untuk karyawan yang sempat bekerja di dashboard, bukan saat token tidak pernah diterima.
    var farewellName by rememberSaveable { mutableStateOf<String?>(null) }
    var farewell by rememberSaveable { mutableStateOf(false) }
    LaunchedEffect(farewell) {
        if (farewell) {
            delay(WelcomeHoldMillis)
            farewell = false
        }
    }

    // Karyawan dilepas: keluar lewat tombol, token ditolak server, atau tidak pernah diterima; QR tampil lagi.
    val unlink: () -> Unit = {
        val leaving = state.connected && userToken != null
        val leavingName = state.userName ?: credential.userName
        userToken?.let(revoke)
        linkedToken = null
        userReleased = true
        scope.launch {
            store.markUnlinked()
            welcomed = false
            if (leaving) {
                farewellName = leavingName
                farewell = true
            }
            onUserExpired()
            epoch++
        }
    }

    if (farewell) {
        OperationalWelcome(userName = farewellName, messages = Res.array.operational_farewell_messages, icon = AppIcons.Moon, modifier = modifier)
    } else if (welcoming) {
        OperationalWelcome(userName = state.userName, messages = Res.array.operational_welcome_messages, icon = AppIcons.Checklist, modifier = modifier)
    } else if (state.connected && userToken == null) {
        OperationalRelink(onRelink = unlink, modifier = modifier)
    } else if (state.connected) {
        // Jarak bilah status dipasang di sini (dan habis dipakai), supaya pita demo tidak menumpuk dengan jam dan kerangka di bawahnya tidak menambah jarak dua kali.
        Column(modifier = modifier.windowInsetsPadding(WindowInsets.statusBars)) {
            DemoBanner(demo)
            SessionExpiryBanner(userToken.orEmpty())
            OperationalDashboard(
                deviceName = credential.name,
                userName = state.userName ?: credential.userName,
                userToken = userToken.orEmpty(),
                deviceToken = credential.token,
                client = client,
                store = offlineStore,
                printers = printers,
                network = network,
                onUserExpired = unlink,
                onSignOut = unlink,
                onSessionOpen = onSessionOpen,
                modifier = Modifier.weight(1f),
            )
        }
    } else {
        OperationalScreen(state = state, onMenu = openMenu, onShowQr = viewModel::showQr, modifier = modifier)
    }

    if (releasing) {
        DeviceCodeSheet(
            title = stringResource(Res.string.device_release_title),
            description = stringResource(Res.string.device_release_description),
            actionLabel = stringResource(Res.string.device_release_action),
            errorText = if (invalid) stringResource(Res.string.device_release_invalid) else null,
            onSubmit = { code ->
                scope.launch {
                    if (store.matches(code)) {
                        userToken?.let(revoke)
                        store.clear()
                        releasing = false
                        onReleased()
                    } else {
                        invalid = true
                    }
                }
            },
            onDismiss = { releasing = false },
        )
    }
}
