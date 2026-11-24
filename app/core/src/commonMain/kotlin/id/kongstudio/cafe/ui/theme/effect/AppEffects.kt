package id.kongstudio.cafe.ui.theme.effect

import androidx.compose.animation.core.CubicBezierEasing
import androidx.compose.animation.core.Easing
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.runtime.Immutable

/** Token gerak dan efek: efek baru ditaruh di folder ini satu berkas satu efek, dan durasi serta kurvanya diambil dari sini. */
@Immutable
class AppEffects(
    /** Umpan balik sentuhan: tekan, pilih, centang. */
    val quickMillis: Int,
    /** Perpindahan elemen: sheet, kartu, pergantian status. */
    val standardMillis: Int,
    /** Masuk layar atau perubahan besar. */
    val slowMillis: Int,
    /** Satu siklus efek yang berulang: napas, kilau. */
    val loopMillis: Int,
    /** Selisih waktu antar item pada kemunculan berurutan. */
    val staggerMillis: Int,
    val standard: Easing,
    val emphasized: Easing,
    /** Melampaui titik akhir sedikit lalu kembali: logo muncul, elemen yang "mendarat". */
    val bounce: Easing,
    /** Mulai lambat, melaju di tengah, berhenti lembut: layar yang pergi. */
    val exit: Easing,
)

val DefaultAppEffects = AppEffects(
    quickMillis = 120,
    standardMillis = 240,
    slowMillis = 400,
    loopMillis = 1_400,
    staggerMillis = 40,
    standard = FastOutSlowInEasing,
    emphasized = CubicBezierEasing(0.2f, 0f, 0f, 1f),
    bounce = CubicBezierEasing(0.34f, 1.45f, 0.5f, 1f),
    exit = CubicBezierEasing(0.7f, 0f, 0.2f, 1f),
)
