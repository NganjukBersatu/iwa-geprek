package id.kongstudio.cafe.feature.stationboard

import id.kongstudio.cafe.core.time.ServerClock
import id.kongstudio.cafe.offline.OfflineStore

private const val MutedKey = "stationboard.sound.muted"
private const val Separator = ","

/** Stasiun yang bunyi menu barunya dimatikan, disimpan di tablet supaya tetap sama setelah aplikasi dibuka ulang. */
internal class StationSoundPrefs(private val store: OfflineStore) {
    suspend fun muted(): Set<String> =
        runCatching { store.getCache(MutedKey)?.body }.getOrNull()
            ?.split(Separator)?.filter { it.isNotBlank() }?.toSet()
            .orEmpty()

    suspend fun save(muted: Set<String>) {
        // Gagal menyimpan cukup berarti pilihan ini hilang saat aplikasi dibuka ulang; bunyi tetap mengikuti pilihan selama terbuka.
        runCatching { store.putCache(MutedKey, muted.sorted().joinToString(Separator), ServerClock.nowEpochSeconds()) }
    }
}
