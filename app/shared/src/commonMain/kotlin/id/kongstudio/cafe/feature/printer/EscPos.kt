package id.kongstudio.cafe.feature.printer

private const val Esc = 0x1B
private const val Gs = 0x1D
private const val LineFeed = 0x0A
private const val NoBreakSpace = 0xA0
private const val Space = 0x20
private const val Question = 0x3F
private const val HighestSingleByte = 256
private const val FeedBeforeCut = 4
private const val AlignLeft = 0
private const val AlignCenter = 1
private const val AlignRight = 2

/** Pembangun byte ESC/POS: teks hanya ASCII dan Latin-1 (selain itu menjadi "?") dan spasi tanpa putus diganti spasi biasa. */
class EscPos(private val columns: Int) {
    private val out = ArrayList<Byte>()

    init {
        raw(Esc, '@'.code)
    }

    fun text(value: String): EscPos {
        for (char in value) {
            val code = char.code
            out += when {
                code == NoBreakSpace -> Space.toByte()
                code < HighestSingleByte -> code.toByte()
                else -> Question.toByte()
            }
        }
        return this
    }

    fun line(value: String = ""): EscPos = text(value).raw(LineFeed)

    fun align(center: Boolean = false, right: Boolean = false): EscPos =
        raw(Esc, 'a'.code, if (center) AlignCenter else if (right) AlignRight else AlignLeft)

    fun bold(on: Boolean): EscPos = raw(Esc, 'E'.code, if (on) 1 else 0)

    /** ESC ! [mode]: 0x08 tebal, 0x10 tinggi ganda, 0 kembali normal; sama dengan yang dipakai struk kasir web. */
    fun printMode(mode: Int): EscPos = raw(Esc, '!'.code, mode)

    /** Byte yang sudah jadi (mis. gambar logo), dikirim apa adanya. */
    fun bytes(data: ByteArray): EscPos {
        data.forEach { out += it }
        return this
    }

    /** Satu baris dengan [left] di kiri dan [right] di kanan; teks kiri dipotong bila tidak muat. */
    fun pair(left: String, right: String): EscPos {
        val room = (columns - right.length - 1).coerceAtLeast(1)
        val shown = if (left.length > room) left.take(room) else left
        return line(shown + " ".repeat((columns - shown.length - right.length).coerceAtLeast(1)) + right)
    }

    fun divider(): EscPos = line("-".repeat(columns))

    /** Teks panjang dipecah per baris sesuai lebar kertas. */
    fun wrapped(value: String): EscPos {
        value.chunked(columns).forEach { line(it) }
        return this
    }

    fun feed(lines: Int = FeedBeforeCut): EscPos {
        repeat(lines) { raw(LineFeed) }
        return this
    }

    /** Potong kertas parsial, setelah memberi ruang agar tulisan terakhir tidak ikut terpotong. */
    fun cut(): EscPos = feed().raw(Gs, 'V'.code, 1)

    fun build(): ByteArray = out.toByteArray()

    private fun raw(vararg codes: Int): EscPos {
        codes.forEach { out += it.toByte() }
        return this
    }
}
