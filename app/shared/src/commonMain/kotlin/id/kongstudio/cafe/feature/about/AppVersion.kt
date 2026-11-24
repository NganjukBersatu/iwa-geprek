package id.kongstudio.cafe.feature.about

import androidx.compose.runtime.Composable

/** Versi aplikasi yang terpasang dari paketnya, berbentuk "nama (nomor build)". */
@Composable
internal expect fun appVersionLabel(): String

/** Nama versi aplikasi yang terpasang, misalnya "0.1.3". */
@Composable
internal expect fun appVersionName(): String
