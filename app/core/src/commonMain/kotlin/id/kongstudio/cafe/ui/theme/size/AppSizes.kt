package id.kongstudio.cafe.ui.theme.size

import androidx.compose.runtime.Immutable
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

/** Ukuran bersama selain jarak: ikon, garis tepi, kontrol, avatar, dan lebar tata letak. */
@Immutable
class AppSizes(
    val iconSmall: Dp,
    val icon: Dp,
    val iconLarge: Dp,
    val iconXLarge: Dp,
    val borderThin: Dp,
    val borderField: Dp,
    val borderThick: Dp,
    /** Kontrol kecil di dalam kontrol lain (lingkaran stepper). */
    val controlSmall: Dp,
    /** Kontrol sedang yang ditekan (chip, tombol stepper, tombol tambah). */
    val control: Dp,
    val avatarSmall: Dp,
    val avatarLarge: Dp,
    val logo: Dp,
    /** Lebar maksimum isi halaman agar tetap terbaca di layar lebar. */
    val contentMaxWidth: Dp,
    val sidePanelWidth: Dp,
    /** Tinggi bingkai foto di halaman detail menu. */
    val photoPreviewHeight: Dp,
    /** Lebar panel Pesanan di kasir, sudah termasuk jarak luar panel. */
    val orderPanelWidth: Dp,
    val railWidth: Dp,
    val railCollapsedWidth: Dp,
    val cardMinWidth: Dp,
    /** Sisi kotak pratinjau satu lampiran foto atau video di deretan lampiran. */
    val thumbnail: Dp,
    /** Rasio lebar : tinggi foto orang (selfie absen); foto kecil selalu dipotong ke rasio ini. */
    val photoAspectRatio: Float,
    /** Tinggi alami banner dasbor (kartu pengguna dan kartu kehadiran), acuan skala blok dasbor. */
    val bannerBaseline: Dp,
    /** Tinggi alami satu ubin dasbor (angka atau tugas), acuan skala blok dasbor. */
    val tileBaseline: Dp,
    /** Lebar maksimum kode QR yang dipindai dari layar. */
    val qrMaxWidth: Dp,
    /** Tebal garis progres tanpa persen di atas daftar yang sedang dimuat. */
    val progressLine: Dp,
)

val DefaultAppSizes = AppSizes(
    iconSmall = 20.dp,
    icon = 24.dp,
    iconLarge = 28.dp,
    iconXLarge = 40.dp,
    borderThin = 1.dp,
    borderField = 1.5.dp,
    borderThick = 2.dp,
    controlSmall = 32.dp,
    control = 40.dp,
    avatarSmall = 28.dp,
    avatarLarge = 64.dp,
    logo = 36.dp,
    contentMaxWidth = 640.dp,
    sidePanelWidth = 360.dp,
    photoPreviewHeight = 240.dp,
    orderPanelWidth = 420.dp,
    railWidth = 224.dp,
    railCollapsedWidth = 72.dp,
    cardMinWidth = 140.dp,
    thumbnail = 88.dp,
    photoAspectRatio = 3f / 4f,
    bannerBaseline = 252.dp,
    // Tidak boleh di bawah tinggi isi ubin (jarak 2x12, ikon 36, jarak 2x4, label 18, nilai 35 = 121): lebih rendah dari itu baris nilai terjepit dan ekor hurufnya terpotong.
    tileBaseline = 124.dp,
    qrMaxWidth = 300.dp,
    progressLine = 3.dp,
)
