package id.kongstudio.cafe.core.image

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Matrix
import android.graphics.Paint
import android.graphics.Typeface
import android.text.TextPaint
import android.media.ExifInterface
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream

/** Sisi terpanjang hasil konversi; cukup jelas sebagai bukti. */
private const val MAX_SIDE_PX = 1920
private const val JPEG_QUALITY = 85
private const val MIN_QUALITY = 50
private const val QUALITY_STEP = 10
private const val MIN_SIDE_PX = 640
private const val SHRINK_FACTOR = 0.8f

/** Di bawah 2 MB, batas terketat di server (foto profil), supaya hasilnya diterima di mana pun. */
private const val MAX_BYTES = 1_800_000

// Ukuran cap mengikuti PWA: satuan dasar untuk foto selebar 720 px, membesar mengikuti lebar foto.
private const val STAMP_BASE_WIDTH = 720f
private const val STAMP_PADDING = 12f
private const val STAMP_LINE_HEIGHT = 21f
private const val STAMP_TEXT_SIZE = 14f
private const val STAMP_BOLD_TEXT_SIZE = 16f

actual object PhotoConverter {
    actual suspend fun toUploadJpeg(raw: ByteArray): ByteArray? = withContext(Dispatchers.Default) {
        runCatching { convert(raw) }.getOrNull()
    }

    actual suspend fun stamp(jpeg: ByteArray, stamp: PhotoStamp): ByteArray? = withContext(Dispatchers.Default) {
        runCatching {
            val decoded = BitmapFactory.decodeByteArray(jpeg, 0, jpeg.size) ?: return@runCatching null
            val canvasBitmap = decoded.copy(Bitmap.Config.ARGB_8888, true)
            drawStamp(canvasBitmap, stamp)
            shrinkToLimit(canvasBitmap, 0f)
        }.getOrNull()
    }

    private fun drawStamp(bitmap: Bitmap, stamp: PhotoStamp) {
        val canvas = Canvas(bitmap)
        val unit = maxOf(1f, bitmap.width / STAMP_BASE_WIDTH)
        val padding = STAMP_PADDING * unit
        val lineHeight = STAMP_LINE_HEIGHT * unit
        val textWidth = bitmap.width - padding * 2
        val paints = mapOf(
            false to TextPaint(Paint.ANTI_ALIAS_FLAG).apply {
                color = stamp.textArgb
                textSize = STAMP_TEXT_SIZE * unit
            },
            true to TextPaint(Paint.ANTI_ALIAS_FLAG).apply {
                color = stamp.textArgb
                textSize = STAMP_BOLD_TEXT_SIZE * unit
                typeface = Typeface.DEFAULT_BOLD
            },
        )
        val wrapped = stamp.lines.flatMap { line -> wrap(line.text, paints.getValue(line.bold), textWidth).map { it to line.bold } }
        val boxHeight = wrapped.size * lineHeight + padding * 2
        val top = bitmap.height - boxHeight
        canvas.drawRect(0f, top, bitmap.width.toFloat(), bitmap.height.toFloat(), Paint().apply { color = stamp.backgroundArgb })
        wrapped.forEachIndexed { index, (text, bold) ->
            val paint = paints.getValue(bold)
            canvas.drawText(text, padding, top + padding + index * lineHeight - paint.ascent(), paint)
        }
    }

    /** Memecah [text] per kata agar setiap potongan muat di [width]. */
    private fun wrap(text: String, paint: Paint, width: Float): List<String> {
        val lines = mutableListOf<String>()
        var current = ""
        for (word in text.split(' ')) {
            val candidate = if (current.isEmpty()) word else "$current $word"
            if (current.isNotEmpty() && paint.measureText(candidate) > width) {
                lines += current
                current = word
            } else {
                current = candidate
            }
        }
        if (current.isNotEmpty()) lines += current
        return lines
    }

    private fun convert(raw: ByteArray): ByteArray? {
        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeByteArray(raw, 0, raw.size, bounds)
        if (bounds.outWidth <= 0 || bounds.outHeight <= 0) return null

        var sample = 1
        while (maxOf(bounds.outWidth, bounds.outHeight) / (sample * 2) >= MAX_SIDE_PX) sample *= 2
        val decoded = BitmapFactory.decodeByteArray(
            raw,
            0,
            raw.size,
            BitmapFactory.Options().apply { inSampleSize = sample },
        ) ?: return null

        return shrinkToLimit(decoded, rotationOf(raw))
    }

    /** Menurunkan mutu lalu ukuran sampai di bawah [MAX_BYTES]. */
    private fun shrinkToLimit(source: Bitmap, rotation: Float): ByteArray {
        var side = minOf(MAX_SIDE_PX, maxOf(source.width, source.height))
        var quality = JPEG_QUALITY
        while (true) {
            val bytes = encode(source, side, quality, rotation)
            if (bytes.size <= MAX_BYTES || (side <= MIN_SIDE_PX && quality <= MIN_QUALITY)) return bytes
            if (quality > MIN_QUALITY) quality -= QUALITY_STEP else side = (side * SHRINK_FACTOR).toInt()
        }
    }

    private fun encode(source: Bitmap, side: Int, quality: Int, rotation: Float): ByteArray {
        val scale = side.toFloat() / maxOf(source.width, source.height)
        val matrix = Matrix().apply {
            if (scale < 1f) postScale(scale, scale)
            if (rotation != 0f) postRotate(rotation)
        }
        val result = Bitmap.createBitmap(source, 0, 0, source.width, source.height, matrix, true)
        return ByteArrayOutputStream().use { out ->
            result.compress(Bitmap.CompressFormat.JPEG, quality, out)
            out.toByteArray()
        }
    }

    private fun rotationOf(raw: ByteArray): Float {
        val orientation = runCatching {
            ExifInterface(ByteArrayInputStream(raw))
                .getAttributeInt(ExifInterface.TAG_ORIENTATION, ExifInterface.ORIENTATION_NORMAL)
        }.getOrDefault(ExifInterface.ORIENTATION_NORMAL)
        return when (orientation) {
            ExifInterface.ORIENTATION_ROTATE_90 -> 90f
            ExifInterface.ORIENTATION_ROTATE_180 -> 180f
            ExifInterface.ORIENTATION_ROTATE_270 -> 270f
            else -> 0f
        }
    }
}
