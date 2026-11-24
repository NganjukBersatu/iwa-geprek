package id.kongstudio.cafe.feature.operational

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import id.kongstudio.cafe.core.time.ServerClock
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.session_expiring
import id.kongstudio.cafe.ui.component.statusbanner.BannerTone
import id.kongstudio.cafe.ui.component.statusbanner.StatusBanner
import kotlin.io.encoding.Base64
import kotlin.io.encoding.ExperimentalEncodingApi
import kotlinx.coroutines.delay
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.longOrNull
import org.jetbrains.compose.resources.stringResource

private const val WarnSeconds = 60L
private const val TickMillis = 1_000L

/** Waktu habis sesi (detik epoch) dari klaim exp pada token; null bila token tidak terbaca. */
@OptIn(ExperimentalEncodingApi::class)
internal fun tokenExpiryEpoch(token: String): Long? = runCatching {
    val payload = token.split('.')[1]
    val json = Base64.UrlSafe.withPadding(Base64.PaddingOption.ABSENT_OPTIONAL).decode(payload).decodeToString()
    Json.parseToJsonElement(json).jsonObject["exp"]?.jsonPrimitive?.longOrNull
}.getOrNull()

/** Peringatan hitung mundur menjelang sesi karyawan habis, supaya pekerjaan sempat diselesaikan. */
@Composable
internal fun SessionExpiryBanner(token: String) {
    val expiry = remember(token) { tokenExpiryEpoch(token) } ?: return
    var left by remember(token) { mutableLongStateOf(expiry - ServerClock.nowEpochSeconds()) }
    LaunchedEffect(token) {
        while (left > 0) {
            delay(if (left > WarnSeconds) (left - WarnSeconds) * TickMillis else TickMillis)
            left = expiry - ServerClock.nowEpochSeconds()
        }
    }
    if (left in 1..WarnSeconds) {
        StatusBanner(text = stringResource(Res.string.session_expiring, left), tone = BannerTone.Warning)
    }
}
