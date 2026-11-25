package id.kongstudio.cafe

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.lifecycle.compose.LifecycleResumeEffect
import coil3.ImageLoader
import coil3.SingletonImageLoader
import coil3.compose.LocalPlatformContext
import coil3.compose.setSingletonImageLoaderFactory
import coil3.network.ktor3.KtorNetworkFetcherFactory
import id.kongstudio.cafe.core.network.ApiConfig
import id.kongstudio.cafe.core.network.ImageAccess
import id.kongstudio.cafe.core.network.createImageClient
import id.kongstudio.cafe.core.network.createApiClient
import id.kongstudio.cafe.feature.about.appVersionName
import id.kongstudio.cafe.feature.auth.login.KtorLoginRepository
import id.kongstudio.cafe.feature.auth.login.LoginRoute
import id.kongstudio.cafe.feature.auth.session.LoginSession
import id.kongstudio.cafe.feature.auth.session.SessionRevoker
import id.kongstudio.cafe.feature.auth.session.SessionStore
import id.kongstudio.cafe.feature.devicesetup.DeviceCredential
import id.kongstudio.cafe.feature.devicesetup.DeviceModeStore
import id.kongstudio.cafe.feature.devicesetup.DevicePairingResult
import id.kongstudio.cafe.feature.devicesetup.KtorDevicePairingRepository
import id.kongstudio.cafe.feature.home.HomeRoute
import id.kongstudio.cafe.feature.location.DeviceLocation
import id.kongstudio.cafe.feature.network.NetworkMonitor
import id.kongstudio.cafe.feature.operational.OperationalRoute
import id.kongstudio.cafe.feature.permission.DevicePermissions
import id.kongstudio.cafe.feature.permission.PermissionGateRoute
import id.kongstudio.cafe.feature.permission.PermissionPurpose
import id.kongstudio.cafe.feature.printer.ThermalPrinters
import id.kongstudio.cafe.feature.update.AppUpdate
import id.kongstudio.cafe.feature.update.UpdateGate
import id.kongstudio.cafe.feature.demo.DemoMode
import id.kongstudio.cafe.offline.OfflineStore
import id.kongstudio.cafe.ui.component.splashscreen.SplashScreen
import id.kongstudio.cafe.ui.theme.AppTheme
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.launch

@Composable
fun App(
    sessionStore: SessionStore,
    permissions: DevicePermissions,
    deviceModeStore: DeviceModeStore,
    offlineStore: OfflineStore,
    location: DeviceLocation,
    printers: ThermalPrinters,
    network: NetworkMonitor,
) {
    AppTheme {
        var session by remember { mutableStateOf<LoginSession?>(null) }
        var device by remember { mutableStateOf<DeviceCredential?>(null) }
        var restored by remember { mutableStateOf(false) }
        val scope = rememberCoroutineScope()
        val current = session
        val installed = appVersionName()
        val update = remember { AppUpdate(installed) }
        val demo = remember { DemoMode() }
        val client = remember { createApiClient(installed, update::refused, demo::observe) }
        val pairing = remember { KtorDevicePairingRepository(client, ApiConfig.V2_BASE_URL) }
        val revoker = remember { SessionRevoker(client, ApiConfig.V2_BASE_URL, sessionStore) }
        val revoke: (String) -> Unit = { token -> scope.launch { revoker.revoke(token) } }

        // Foto nota, absen, dan lampiran dibuka server hanya untuk yang berhak, jadi pemuat gambar ikut mengirim token pemakai yang sedang aktif.
        val imageAccess = remember { ImageAccess() }
        val platform = LocalPlatformContext.current
        setSingletonImageLoaderFactory { context ->
            ImageLoader.Builder(context)
                .components { add(KtorNetworkFetcherFactory(createImageClient(ApiConfig.V2_BASE_URL, imageAccess))) }
                .build()
        }
        val identity = device?.token ?: current?.accessToken
        imageAccess.use(identity)
        LaunchedEffect(identity) {
            // Gambar milik pemakai sebelumnya tidak tersisa di perangkat setelah keluar.
            if (identity == null) {
                val loader = SingletonImageLoader.get(platform)
                loader.memoryCache?.clear()
                loader.diskCache?.clear()
            }
        }

        LaunchedEffect(Unit) {
            session = sessionStore.load()
            device = deviceModeStore.load()
            restored = true
            // Memuat sesi bisa mengantrekan token dari sesi usang, yang belum tertangkap pengiriman pertama aliran online.
            revoker.flush()
        }
        LaunchedEffect(Unit) {
            network.online.collect { online -> if (online) revoker.flush() }
        }
        // Versi minimum dibaca saat aplikasi dibuka dan kembali ke layar; tanpa polling.
        LifecycleResumeEffect(update) {
            val check = scope.launch { update.check(client, ApiConfig.V2_BASE_URL) }
            onPauseOrDispose { check.cancel() }
        }
        // Penolakan 426 belum membawa versi minimum dan alamat unduhan, jadi keduanya dibaca sekali sesudahnya.
        LaunchedEffect(update) {
            update.state.map { it.required && it.minimum == null }.distinctUntilChanged().collect { missing ->
                if (missing) update.check(client, ApiConfig.V2_BASE_URL)
            }
        }

        SplashScreen(ready = restored) {
            if (device != null) {
                PermissionGateRoute(permissions, PermissionPurpose.Operational) {
                    OperationalRoute(
                        credential = device!!,
                        client = client,
                        store = deviceModeStore,
                        offlineStore = offlineStore,
                        printers = printers,
                        network = network,
                        revoke = revoke,
                        onReleased = {
                            device = null
                            scope.launch { deviceModeStore.clear() }
                        },
                        onUserExpired = {
                            scope.launch { device = deviceModeStore.load() }
                        },
                        onSessionOpen = update::sessionOpen,
                        demo = demo,
                    )
                }
            } else if (current == null) {
                LoginRoute(
                    repository = remember { KtorLoginRepository(client, ApiConfig.V2_BASE_URL) },
                    onLoggedIn = {
                        session = it
                        scope.launch { sessionStore.save(it) }
                    },
                    onRegisterDevice = { code ->
                        val result = pairing.pair(code, deviceModeStore.deviceInfo())
                        if (result is DevicePairingResult.Paired) {
                            deviceModeStore.save(result.credential, code)
                            device = result.credential
                        }
                        result
                    },
                    permissions = permissions,
                )
            } else {
                PermissionGateRoute(permissions, PermissionPurpose.Attendance) {
                    HomeRoute(
                        session = current,
                        client = client,
                        location = location,
                        network = network,
                        onLogout = {
                            session = null
                            scope.launch { sessionStore.clear() }
                            revoke(current.accessToken)
                        },
                    )
                }
            }
        }
        UpdateGate(update)
    }
}
