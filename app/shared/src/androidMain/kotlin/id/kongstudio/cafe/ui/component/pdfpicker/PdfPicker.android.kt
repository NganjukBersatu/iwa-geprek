package id.kongstudio.cafe.ui.component.pdfpicker

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Paint
import android.graphics.Rect
import android.graphics.pdf.PdfDocument
import android.graphics.pdf.PdfRenderer
import android.net.Uri
import android.os.ParcelFileDescriptor
import android.provider.OpenableColumns
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import id.kongstudio.cafe.ui.theme.color.LightAppColors
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.ByteArrayOutputStream
import java.io.File

private const val PDF_MIME = "application/pdf"
private const val FALLBACK_NAME = "lampiran.pdf"
private const val PDF_DIR = "pdfs"

// Halaman digambar ulang mulai 1,5x ukuran titik PDF (sekitar 108 dpi), lalu diperkecil bertahap sampai muat.
private const val START_SCALE = 1.5f
private const val SCALE_STEP = 0.8f
private const val MIN_SCALE = 0.25f

@Composable
actual fun rememberPdfPicker(onPicked: (PickedPdf) -> Unit): PdfPicker {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val picked = rememberUpdatedState(onPicked)
    // Penanda pemilih sedang terbuka, agar ketukan berulang tidak membuka pemilih kedua.
    var open by rememberSaveable { mutableStateOf(false) }

    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        open = false
        if (uri == null) return@rememberLauncherForActivityResult
        scope.launch { readPdf(context, uri)?.let(picked.value) }
    }

    return remember(launcher) {
        object : PdfPicker {
            override fun pick() {
                if (open) return
                // Tanpa aplikasi pemilih berkas yang bisa dibuka, ketukan tidak berbuat apa-apa, bukan menutup aplikasi.
                open = runCatching { launcher.launch(arrayOf(PDF_MIME)) }.isSuccess
            }
        }
    }
}

private suspend fun readPdf(context: Context, uri: Uri): PickedPdf? = withContext(Dispatchers.IO) {
    val bytes = runCatching { context.contentResolver.openInputStream(uri)?.use { it.readBytes() } }.getOrNull()
        ?: return@withContext null
    val fitted = if (bytes.size > MaxPdfBytes) shrink(context, bytes) ?: bytes else bytes
    PickedPdf(fitted, nameOf(context, uri))
}

/** Menggambar ulang setiap halaman sebagai gambar dengan resolusi yang terus diturunkan sampai PDF muat di batas. */
private fun shrink(context: Context, bytes: ByteArray): ByteArray? {
    val dir = File(context.cacheDir, PDF_DIR).apply { mkdirs() }
    val source = File.createTempFile("source_", ".pdf", dir)
    return try {
        source.writeBytes(bytes)
        ParcelFileDescriptor.open(source, ParcelFileDescriptor.MODE_READ_ONLY).use { descriptor ->
            PdfRenderer(descriptor).use { renderer ->
                var scale = START_SCALE
                var result = redraw(renderer, scale)
                while (result.size > MaxPdfBytes && scale > MIN_SCALE) {
                    scale *= SCALE_STEP
                    result = redraw(renderer, scale)
                }
                result
            }
        }
    } catch (_: Exception) {
        null
    } finally {
        source.delete()
    }
}

private fun redraw(renderer: PdfRenderer, scale: Float): ByteArray {
    val document = PdfDocument()
    val paint = Paint(Paint.FILTER_BITMAP_FLAG)
    val paper = LightAppColors.surface.toArgb()
    try {
        for (index in 0 until renderer.pageCount) {
            renderer.openPage(index).use { page ->
                val bitmap = Bitmap.createBitmap(
                    maxOf(1, (page.width * scale).toInt()),
                    maxOf(1, (page.height * scale).toInt()),
                    Bitmap.Config.ARGB_8888,
                )
                bitmap.eraseColor(paper)
                page.render(bitmap, null, null, PdfRenderer.Page.RENDER_MODE_FOR_PRINT)
                val target = document.startPage(PdfDocument.PageInfo.Builder(page.width, page.height, index + 1).create())
                target.canvas.drawBitmap(bitmap, null, Rect(0, 0, page.width, page.height), paint)
                document.finishPage(target)
                bitmap.recycle()
            }
        }
        return ByteArrayOutputStream().use { out ->
            document.writeTo(out)
            out.toByteArray()
        }
    } finally {
        document.close()
    }
}

private fun nameOf(context: Context, uri: Uri): String =
    runCatching {
        context.contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { cursor ->
            if (cursor.moveToFirst()) cursor.getString(0) else null
        }
    }.getOrNull() ?: FALLBACK_NAME
