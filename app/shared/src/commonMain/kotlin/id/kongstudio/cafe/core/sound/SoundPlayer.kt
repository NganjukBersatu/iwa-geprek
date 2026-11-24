package id.kongstudio.cafe.core.sound

import androidx.compose.runtime.Composable

/** Suara pendek aplikasi; berkasnya di composeResources/files/sounds milik core, dan [alarm] memutarnya di volume alarm supaya terdengar di dapur. */
enum class AppSound(val path: String, val alarm: Boolean = false) {
    PaymentSuccess("files/sounds/pembayaran-berhasil.mp3"),

    // Alarm_Beep_03 dari AOSP frameworks/base/data/sounds, lisensi Apache 2.0.
    OrderArrived("files/sounds/order-arrived.ogg", alarm = true),
}

/** Memutar suara tanpa pernah melempar galat: perangkat tanpa audio atau berkas rusak cukup diam, karena suara hanya pemanis. */
fun interface SoundPlayer {
    fun play(sound: AppSound)
}

@Composable
expect fun rememberSoundPlayer(): SoundPlayer
