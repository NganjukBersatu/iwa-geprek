package id.kongstudio.cafe.ui.component.qrcode

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import id.kongstudio.cafe.ui.theme.AppTheme

/** Kotak modul QR: [dark] berisi [size] x [size] modul, baris demi baris. */
internal class QrModules(val size: Int, val dark: BooleanArray)

/** Gambar QR persegi dari [content]; modul gelap memakai warna isi, latar putih dengan tepi tenang. */
@Composable
fun QrCode(
    content: String,
    modifier: Modifier = Modifier,
) {
    val modules = remember(content) { qrModules(content) }
    val ink = AppTheme.colors.content

    Canvas(
        modifier = modifier
            .aspectRatio(1f)
            .background(AppTheme.colors.surface)
            .padding(AppTheme.spacing.md),
    ) {
        val cell = size.width / modules.size
        for (row in 0 until modules.size) {
            for (col in 0 until modules.size) {
                if (modules.dark[row * modules.size + col]) {
                    drawRect(
                        color = ink,
                        topLeft = Offset(col * cell, row * cell),
                        size = Size(cell + 0.5f, cell + 0.5f),
                    )
                }
            }
        }
    }
}

/** Mengubah [content] menjadi kotak modul QR; diimplementasikan per platform. */
internal expect fun qrModules(content: String): QrModules
