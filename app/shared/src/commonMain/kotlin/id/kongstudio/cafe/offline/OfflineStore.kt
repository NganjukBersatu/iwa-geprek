package id.kongstudio.cafe.offline

import app.cash.sqldelight.coroutines.asFlow
import app.cash.sqldelight.coroutines.mapToList
import app.cash.sqldelight.db.SqlDriver
import id.kongstudio.cafe.offline.db.OfflineDatabase
import id.kongstudio.cafe.offline.db.PendingOrder
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.withContext

private const val StatusQueued = "queued"
private const val StatusRejected = "rejected"
private const val StatusNeedsLogin = "needs_login"

/** Keadaan satu pesanan di antrean tablet. */
internal enum class QueueStatus { Queued, NeedsLogin, Rejected }

internal class QueuedOrder(
    val clientId: String,
    val userId: String,
    val payload: String,
    val createdEpoch: Long,
    val total: Long,
    val itemCount: Int,
    val message: String?,
    val status: QueueStatus = QueueStatus.Queued,
    /** Berapa kali server sudah dicoba untuk pesanan ini. */
    val attempts: Int = 0,
)

/** Jumlah pesanan per keadaan; [needsLogin] menunggu karyawan pembuatnya memindai QR lagi. */
internal data class QueueCounts(val queued: Int = 0, val rejected: Int = 0, val needsLogin: Int = 0) {
    val isEmpty: Boolean get() = queued == 0 && rejected == 0 && needsLogin == 0

    /** Pesanan yang masih akan terkirim sendiri, beda dengan yang ditolak dan butuh keputusan. */
    val sending: Int get() = queued + needsLogin
}

internal class CachedBody(val body: String, val savedEpoch: Long)

/** Penyimpanan lokal tahan-lama untuk antrean pesanan dan hasil baca terakhir, dengan pesanan hanya dibuang lewat [delete] setelah diterima server atau atas keputusan karyawan. */
class OfflineStore(driver: SqlDriver) {
    private val database = OfflineDatabase(driver)
    private val orders = database.pendingOrderQueries
    private val cache = database.cacheEntryQueries

    internal suspend fun enqueue(
        clientId: String,
        userId: String,
        payload: String,
        createdEpoch: Long,
        total: Long,
        itemCount: Int,
    ) = withContext(Dispatchers.Default) {
        orders.insert(clientId, userId, payload, createdEpoch, total, itemCount.toLong())
    }

    internal suspend fun queuedFor(userId: String): List<QueuedOrder> = withContext(Dispatchers.Default) {
        orders.selectQueuedForUser(userId).executeAsList().map { it.toModel() }
    }

    internal suspend fun rejected(): List<QueuedOrder> = withContext(Dispatchers.Default) {
        orders.selectRejected().executeAsList().map { it.toModel() }
    }

    /** Semua pesanan di antrean tablet, terlama dulu, diikuti setiap kali antrean berubah. */
    internal fun all(): Flow<List<QueuedOrder>> =
        orders.selectAll().asFlow().mapToList(Dispatchers.Default).map { rows -> rows.map { it.toModel() } }

    internal fun counts(): Flow<QueueCounts> =
        orders.countByStatus().asFlow().mapToList(Dispatchers.Default).map { rows ->
            countsOf(rows.map { it.status to it.total })
        }

    /** Antrean milik satu karyawan saja, supaya antrean kasir lain di tablet yang sama tidak ikut menahan. */
    internal fun countsFor(userId: String): Flow<QueueCounts> =
        orders.countByStatusForUser(userId).asFlow().mapToList(Dispatchers.Default).map { rows ->
            countsOf(rows.map { it.status to it.total })
        }

    private fun countsOf(rows: List<Pair<String, Long>>): QueueCounts {
        fun of(status: String) = rows.firstOrNull { it.first == status }?.second?.toInt() ?: 0
        return QueueCounts(of(StatusQueued), of(StatusRejected), of(StatusNeedsLogin))
    }

    internal suspend fun markRejected(clientId: String, message: String?) = withContext(Dispatchers.Default) {
        orders.markStatus(StatusRejected, message, clientId)
    }

    internal suspend fun markNeedsLogin(clientId: String) = withContext(Dispatchers.Default) {
        orders.markStatus(StatusNeedsLogin, null, clientId)
    }

    /** Percobaan yang gagal karena jaringan atau server tetap menunggu, hanya hitungannya yang naik. */
    internal suspend fun markAttempt(clientId: String) = withContext(Dispatchers.Default) {
        orders.markStatus(StatusQueued, null, clientId)
    }

    internal suspend fun requeue(clientId: String) = withContext(Dispatchers.Default) {
        orders.requeue(clientId)
    }

    internal suspend fun requeueNeedsLogin(userId: String) = withContext(Dispatchers.Default) {
        orders.requeueNeedsLogin(userId)
    }

    internal suspend fun delete(clientId: String) = withContext(Dispatchers.Default) {
        orders.delete(clientId)
    }

    internal suspend fun putCache(key: String, body: String, savedEpoch: Long) = withContext(Dispatchers.Default) {
        cache.upsert(key, body, savedEpoch)
    }

    internal suspend fun getCache(key: String): CachedBody? = withContext(Dispatchers.Default) {
        cache.select(key).executeAsOneOrNull()?.let { CachedBody(it.body, it.saved_epoch) }
    }

    private fun PendingOrder.toModel() = QueuedOrder(
        clientId = client_id,
        userId = user_id,
        payload = payload,
        createdEpoch = created_epoch,
        total = total,
        itemCount = item_count.toInt(),
        message = message,
        status = when (status) {
            StatusRejected -> QueueStatus.Rejected
            StatusNeedsLogin -> QueueStatus.NeedsLogin
            else -> QueueStatus.Queued
        },
        attempts = attempts.toInt(),
    )
}
