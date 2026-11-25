package id.kongstudio.cafe.feature.demo

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.demo_mode_banner
import id.kongstudio.cafe.ui.component.statusbanner.BannerTone
import id.kongstudio.cafe.ui.component.statusbanner.StatusBanner
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import org.jetbrains.compose.resources.stringResource

/** Satu sumber "sistem sedang di mode demo" di aplikasi: diisi dari header setiap jawaban server, lalu diamati kerangka layar. */
internal class DemoMode {
    private val _active = MutableStateFlow(false)
    val active: StateFlow<Boolean> = _active.asStateFlow()

    /** Jawaban berheader demo berarti demo menyala; jawaban tanpa header berarti sudah kembali ke data asli. */
    fun observe(active: Boolean) {
        _active.value = active
    }
}

/** Pita kecil di atas layar operasional selama mode demo, tanpa tombol keluar; keluar hanya dari web admin oleh pemilik. */
@Composable
internal fun DemoBanner(demo: DemoMode) {
    val active by demo.active.collectAsState()
    if (active) {
        StatusBanner(text = stringResource(Res.string.demo_mode_banner), tone = BannerTone.Info)
    }
}
