package id.kongstudio.cafe.ui.theme.color

import androidx.compose.runtime.Immutable
import androidx.compose.ui.graphics.Color

@Immutable
class AppColors(
    val background: Color,
    val surface: Color,
    val surfaceAccent: Color,
    /** Aksen pekat untuk penanda: garis tepi, indikator, seri grafik, dan bintang; tidak pernah menjadi latar teks. */
    val accent: Color,
    /** Latar aksen muda untuk wadah yang memuat teks atau ikon [content], supaya kontrasnya terjaga berapa pun warna aksen merek. */
    val accentSurface: Color,
    val outline: Color,
    val primary: Color,
    val onPrimary: Color,
    /** Teks sekunder di atas wadah primary. */
    val onPrimaryMuted: Color,
    /** Latar lembut di atas wadah primary (avatar). */
    val onPrimarySubtle: Color,
    val content: Color,
    val contentMuted: Color,
    val divider: Color,
    /** Latar gelap di balik pratinjau layar penuh. */
    val scrim: Color,
    val selected: Color,
    val danger: Color,
    val dangerContainer: Color,
    val onDangerContainer: Color,
    val warning: Color,
    val warningContainer: Color,
    /** Kuning untuk hal yang belum lengkap diatur, seperti menu tanpa resep; dipakai solid dan teks di atasnya memakai content. */
    val caution: Color,
    val info: Color,
    val success: Color,
    /** Penanda kategori yang tidak bermakna status, misalnya warna tahap papan pesanan. */
    val violet: Color,
    val rose: Color,
    /** Opasitas kontrol yang dinonaktifkan. */
    val disabledAlpha: Float,
)

val LightAppColors = AppColors(
    // Palet merek dari BrandColors, sama dengan token web.
    background = BrandColors.soft,
    surface = Color(0xFFFFFFFF),
    surfaceAccent = BrandColors.tint,
    accent = BrandColors.accent,
    accentSurface = BrandColors.accentSoft,
    outline = BrandColors.line,
    primary = BrandColors.primary,
    onPrimary = BrandColors.onPrimary,
    onPrimaryMuted = Color(0xD9FFFFFF),
    onPrimarySubtle = Color(0x24FFFFFF),
    content = BrandColors.ink,
    contentMuted = BrandColors.muted,
    divider = BrandColors.line,
    scrim = Color(0xE6000000),
    selected = BrandColors.line.copy(alpha = 0.4f),
    danger = Color(0xFFB91C1C),
    dangerContainer = Color(0xFFFEE2E2),
    onDangerContainer = Color(0xFF7F1D1D),
    // Amber-800, keluarga yang sama dengan latarnya, supaya teks peringatan mencapai 4,5:1 di atas warningContainer dan background.
    warning = Color(0xFF92400E),
    warningContainer = Color(0x26B45309),
    caution = Color(0xFFFBBF24),
    info = Color(0xFF1D4ED8),
    success = Color(0xFF0F766E),
    violet = Color(0xFF6D28D9),
    rose = Color(0xFFBE185D),
    disabledAlpha = 0.5f,
)
