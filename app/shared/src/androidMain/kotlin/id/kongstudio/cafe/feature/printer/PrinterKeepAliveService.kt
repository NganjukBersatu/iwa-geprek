package id.kongstudio.cafe.feature.printer

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import androidx.core.app.NotificationCompat
import androidx.core.app.ServiceCompat
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.printer_keep_alive_channel
import id.kongstudio.cafe.resources.printer_keep_alive_notice_text
import id.kongstudio.cafe.resources.printer_keep_alive_notice_title
import kotlinx.coroutines.runBlocking
import org.jetbrains.compose.resources.StringResource
import org.jetbrains.compose.resources.getString

private const val ChannelId = "printer_keep_alive"
private const val NoticeId = 4107
// Dipakai bila teks sumber daya tidak terbaca; notifikasi tetap harus jadi supaya startForeground tidak gagal.
private const val FallbackTitle = "Printer tetap tersambung"

/** Menahan proses tetap hidup lewat notifikasi tetap agar sambungan [AndroidThermalPrinters] tidak putus, dan agar tidak force close startForeground selalu dipanggil paling awal, layanan hanya berhenti sendiri tanpa stopService dari luar, serta setiap panggilan sistem yang ditolak berarti berhenti diam-diam. */
class PrinterKeepAliveService : Service() {
    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        running = this
    }

    override fun onDestroy() {
        if (running === this) running = null
        super.onDestroy()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val foreground = runCatching { ServiceCompat.startForeground(this, NoticeId, notice(), connectedDeviceType()) }.isSuccess
        // Juga saat dibuat ulang sistem setelah proses dimatikan: pengelola printer dihidupkan lagi dan menyambung printer tersimpan.
        val printers = runCatching { AndroidThermalPrinters.get(applicationContext) }.getOrNull()
        // Pilihan dimatikan, printer dilepas, atau izin dicabut selagi layanan sedang dimulai: berhenti sesudah foreground.
        if (!foreground || printers?.wantsKeepAlive() != true) {
            stop()
            return START_NOT_STICKY
        }
        return START_STICKY
    }

    private fun stop() {
        runCatching { ServiceCompat.stopForeground(this, ServiceCompat.STOP_FOREGROUND_REMOVE) }
        stopSelf()
    }

    private fun connectedDeviceType(): Int =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) ServiceInfo.FOREGROUND_SERVICE_TYPE_CONNECTED_DEVICE else 0

    private fun text(resource: StringResource, fallback: String): String =
        runCatching { runBlocking { getString(resource) } }.getOrNull()?.takeIf { it.isNotBlank() } ?: fallback

    private fun notice(): Notification {
        val title = text(Res.string.printer_keep_alive_notice_title, FallbackTitle)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            runCatching {
                val channel = NotificationChannel(ChannelId, text(Res.string.printer_keep_alive_channel, FallbackTitle), NotificationManager.IMPORTANCE_LOW)
                getSystemService(NotificationManager::class.java)?.createNotificationChannel(channel)
            }
        }
        val open = runCatching {
            packageManager.getLaunchIntentForPackage(packageName)?.let {
                PendingIntent.getActivity(this, 0, it, PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
            }
        }.getOrNull()
        return NotificationCompat.Builder(this, ChannelId)
            .setSmallIcon(android.R.drawable.stat_sys_data_bluetooth)
            .setContentTitle(title)
            .setContentText(text(Res.string.printer_keep_alive_notice_text, ""))
            .setContentIntent(open)
            .setOngoing(true)
            .setSilent(true)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .build()
    }

    companion object {
        @Volatile
        private var running: PrinterKeepAliveService? = null

        /** Menghentikan layanan dari dalam, sedangkan layanan yang belum berjalan memeriksa pilihannya sendiri dan berhenti sesudah startForeground. */
        internal fun stopRunning() {
            Handler(Looper.getMainLooper()).post { running?.stop() }
        }
    }
}
