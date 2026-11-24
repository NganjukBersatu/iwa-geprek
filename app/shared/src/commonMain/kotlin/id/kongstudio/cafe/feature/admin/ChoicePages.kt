package id.kongstudio.cafe.feature.admin

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.TimeSource
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

private const val SearchDelayMillis = 250L
// Sama dengan Loadable, supaya kerangka tidak berkedip saat server menjawab sangat cepat.
private const val MinSearchShownMillis = 350

/** Satu halaman pilihan; [hasMore] false berarti daftar sudah habis. */
internal class ChoicePage<T>(val items: List<T>, val hasMore: Boolean)

/** Daftar pilihan yang dicari di server dan dimuat per halaman saat digulir, sehingga tidak ada pilihan yang terpotong berapa pun jumlahnya. */
internal class ChoicePages<T>(
    private val scope: CoroutineScope,
    private val key: (T) -> String,
    /** [page] berbasis nol. */
    private val fetch: suspend (query: String, page: Int) -> DeviceResult<ChoicePage<T>>,
) {
    var items by mutableStateOf<List<T>>(emptyList())
        private set

    /** Halaman pertama sedang dicari, termasuk selama jeda ketik; daftar diganti kerangka. */
    var searching by mutableStateOf(true)
        private set

    /** Halaman berikutnya sedang dimuat; daftar tetap, kerangka di ujung bawah. */
    var loadingMore by mutableStateOf(false)
        private set
    var failure by mutableStateOf<AppFailure?>(null)
        private set
    private var query: String? = null
    private var page = 0
    private var hasMore = false
    private var job: Job? = null

    val busy: Boolean get() = searching || loadingMore

    fun search(text: String) {
        val typed = text.trim()
        if (typed == query) return
        query = typed
        job?.cancel()
        loadingMore = false
        searching = true
        val started = TimeSource.Monotonic.markNow()
        job = scope.launch {
            if (typed.isNotEmpty()) delay(SearchDelayMillis)
            val result = fetch(typed, 0)
            val remaining = MinSearchShownMillis.milliseconds - started.elapsedNow()
            if (remaining.isPositive()) delay(remaining)
            apply(result, 0)
            searching = false
        }
    }

    fun more() {
        val typed = query ?: return
        if (!hasMore || job?.isActive == true) return
        loadingMore = true
        job = scope.launch {
            apply(fetch(typed, page + 1), page + 1)
            loadingMore = false
        }
    }

    private fun apply(result: DeviceResult<ChoicePage<T>>, next: Int) {
        when (result) {
            is DeviceResult.Ok -> {
                // Data bisa bergeser di antara dua halaman, jadi pilihan yang sudah tampil tidak diulang.
                items = (if (next == 0) result.value.items else items + result.value.items).distinctBy(key)
                page = next
                hasMore = result.value.hasMore
                failure = null
            }
            is DeviceResult.Failed -> failure = result.failure
        }
    }
}

@Composable
internal fun <T> rememberChoicePages(key: (T) -> String, fetch: suspend (query: String, page: Int) -> DeviceResult<ChoicePage<T>>): ChoicePages<T> {
    val scope = rememberCoroutineScope()
    val pages = remember { ChoicePages(scope, key, fetch) }
    LaunchedEffect(pages) { pages.search("") }
    return pages
}
