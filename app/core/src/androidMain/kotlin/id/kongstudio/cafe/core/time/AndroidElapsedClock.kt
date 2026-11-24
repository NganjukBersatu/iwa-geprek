package id.kongstudio.cafe.core.time

import android.content.Context
import android.os.SystemClock
import android.provider.Settings

/** Jam Android yang ikut berjalan saat tidur (`elapsedRealtime`), dengan hitungan hidup perangkat sebagai penanda dimulai ulang. */
class AndroidElapsedClock(context: Context) : ElapsedClock {
    private val resolver = context.applicationContext.contentResolver

    override fun elapsedMillis(): Long = SystemClock.elapsedRealtime()

    override val bootId: String? by lazy {
        runCatching { Settings.Global.getInt(resolver, Settings.Global.BOOT_COUNT).toString() }.getOrNull()
    }
}
