package id.kongstudio.cafe.feature.printer

/** Kertas sempit menyisakan sekian kolom untuk kata walau lekukan barisnya dalam. */
private const val MinWordRoom = 8
private val Whitespace = Regex("\\s+")

/** Salinan aturan lipat teks kasir web (`bungkusTeks` di frontend/src/lib/printer.ts) yang hanya diubah bersama versi web supaya cetakan keduanya tetap identik. */
fun wrapText(text: String, width: Int): List<String> {
    val result = ArrayList<String>()
    for (paragraph in text.split('\n')) {
        if (paragraph.length <= width) {
            result += paragraph
            continue
        }
        val indent = paragraph.takeWhile { it.isWhitespace() }.take((width - MinWordRoom).coerceAtLeast(0))
        val room = width - indent.length
        var line = ""
        for (whole in paragraph.split(Whitespace).filter { it.isNotEmpty() }) {
            var word = whole
            while (word.length > room) {
                if (line.isNotEmpty()) {
                    result += indent + line
                    line = ""
                }
                result += indent + word.take(room)
                word = word.drop(room)
            }
            when {
                line.isEmpty() -> line = word
                line.length + 1 + word.length <= room -> line += " $word"
                else -> {
                    result += indent + line
                    line = word
                }
            }
        }
        if (line.isNotEmpty()) result += indent + line
    }
    return result
}

/** Label kiri dan nilai rata kanan dalam satu baris (`baris2Kolom` web); jalur kertas 80 mm, jangan diubah. */
fun twoColumns(left: String, right: String, width: Int): String =
    left + " ".repeat((width - left.length - right.length).coerceAtLeast(1)) + right

/** Seperti [twoColumns], tetapi label yang tidak muat dilipat dan nilainya rata kanan di baris terakhir (`baris2KolomLipat` web). */
fun twoColumnsWrapped(left: String, right: String, width: Int): String {
    if (left.length + right.length + 1 <= width) return left + " ".repeat(width - left.length - right.length) + right
    val lines = wrapText(left, width).toMutableList()
    val last = lines.lastOrNull().orEmpty()
    if (last.length + right.length + 1 <= width) {
        lines[lines.lastIndex] = last + " ".repeat(width - last.length - right.length) + right
    } else {
        lines += " ".repeat((width - right.length).coerceAtLeast(0)) + right
    }
    return lines.joinToString("\n")
}
