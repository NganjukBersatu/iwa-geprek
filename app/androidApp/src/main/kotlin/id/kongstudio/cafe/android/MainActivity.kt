package id.kongstudio.cafe.android

import android.os.Bundle
import android.graphics.Color
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import id.kongstudio.cafe.App
import id.kongstudio.cafe.core.time.AndroidElapsedClock
import id.kongstudio.cafe.core.time.ServerClock
import id.kongstudio.cafe.feature.auth.session.AndroidSessionStore
import id.kongstudio.cafe.feature.devicesetup.AndroidDeviceModeStore
import id.kongstudio.cafe.feature.location.AndroidDeviceLocation
import id.kongstudio.cafe.feature.network.AndroidNetworkMonitor
import id.kongstudio.cafe.feature.permission.AndroidDevicePermissions
import id.kongstudio.cafe.feature.printer.AndroidThermalPrinters
import id.kongstudio.cafe.offline.TimeAnchorKeeper
import id.kongstudio.cafe.offline.createOfflineStore

class MainActivity : ComponentActivity() {
    private var network: AndroidNetworkMonitor? = null
    private var printers: AndroidThermalPrinters? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        // Harus sebelum super.onCreate: mengganti tema awal ke tema aplikasi begitu bingkai pertama siap.
        installSplashScreen()
        // Latar aplikasi selalu terang, jadi ikon bar sistem harus gelap.
        val barStyle = SystemBarStyle.light(Color.TRANSPARENT, Color.TRANSPARENT)
        enableEdgeToEdge(statusBarStyle = barStyle, navigationBarStyle = barStyle)
        super.onCreate(savedInstanceState)
        val sessionStore = AndroidSessionStore(applicationContext)
        val permissions = AndroidDevicePermissions(this)
        val deviceModeStore = AndroidDeviceModeStore(applicationContext)
        // Jam yang ikut berjalan saat tidur dipasang sebelum respons pertama dibaca, lalu jangkar waktu terakhir dipulihkan.
        ServerClock.install(AndroidElapsedClock(applicationContext))
        val offlineStore = createOfflineStore(applicationContext)
        TimeAnchorKeeper.start(offlineStore)
        val printers = AndroidThermalPrinters.get(applicationContext).also {
            it.attach(this)
            this.printers = it
        }
        val location = AndroidDeviceLocation(applicationContext)
        val networkMonitor = AndroidNetworkMonitor(applicationContext).also { network = it }
        setContent { App(sessionStore, permissions, deviceModeStore, offlineStore, location, printers, networkMonitor) }
    }

    override fun onDestroy() {
        network?.close()
        printers?.detach(this)
        super.onDestroy()
    }
}
