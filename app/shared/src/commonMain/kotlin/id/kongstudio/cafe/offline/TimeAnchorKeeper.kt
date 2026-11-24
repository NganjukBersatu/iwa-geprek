package id.kongstudio.cafe.offline

import id.kongstudio.cafe.core.time.AnchorSnapshot
import id.kongstudio.cafe.core.time.ServerClock
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

private const val CacheKey = "time_anchor"
private const val Separator = '|'
private const val MillisPerSecond = 1000L
private const val FieldCount = 3

/** Menyimpan jangkar waktu server di penyimpanan lokal dan memulihkannya saat aplikasi mulai, supaya jam yang akurat tetap ada setelah proses dimatikan sistem. */
object TimeAnchorKeeper {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
    private var started = false

    /** Dipanggil sekali saat aplikasi mulai, sesudah [ServerClock.install]; pemanggilan berikutnya (misalnya layar diputar) tidak melakukan apa pun. */
    fun start(store: OfflineStore) {
        if (started) return
        started = true
        scope.launch { restore(store) }
        ServerClock.onAnchored = { snapshot -> scope.launch { remember(store, snapshot) } }
    }

    private suspend fun restore(store: OfflineStore) {
        val body = runCatching { store.getCache(CacheKey) }.getOrNull()?.body ?: return
        val parts = body.split(Separator)
        if (parts.size != FieldCount) return
        val snapshot = AnchorSnapshot(
            serverEpochMillis = parts[0].toLongOrNull() ?: return,
            elapsedAtMillis = parts[1].toLongOrNull() ?: return,
            bootId = parts[2],
        )
        ServerClock.restore(snapshot)
    }

    private suspend fun remember(store: OfflineStore, snapshot: AnchorSnapshot) {
        val body = listOf(snapshot.serverEpochMillis, snapshot.elapsedAtMillis, snapshot.bootId).joinToString(Separator.toString())
        runCatching { store.putCache(CacheKey, body, snapshot.serverEpochMillis / MillisPerSecond) }
    }
}
