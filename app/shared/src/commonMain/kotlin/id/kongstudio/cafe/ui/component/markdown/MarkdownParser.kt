package id.kongstudio.cafe.ui.component.markdown

internal enum class InlineKind { Text, Bold, Italic }

internal class InlineSpan(val kind: InlineKind, val text: String)

internal class CheckItem(val checked: Boolean, val spans: List<InlineSpan>)

internal sealed interface MarkdownBlock {
    class Heading(val level: Int, val spans: List<InlineSpan>) : MarkdownBlock
    class Paragraph(val spans: List<InlineSpan>) : MarkdownBlock
    class Bullets(val items: List<List<InlineSpan>>) : MarkdownBlock
    class Numbers(val items: List<List<InlineSpan>>) : MarkdownBlock
    class Checks(val items: List<CheckItem>) : MarkdownBlock
    class Quote(val spans: List<InlineSpan>) : MarkdownBlock
    data object Divider : MarkdownBlock
    class Picture(val alt: String, val url: String) : MarkdownBlock
    class Video(val alt: String, val url: String) : MarkdownBlock
}

private val heading = Regex("^(#{1,3})\\s+(.*)$")
private val divider = Regex("^---+$")
private val picture = Regex("^!\\[([^\\]]*)\\]\\((https?://\\S+)\\)$")
private val videoFile = Regex("\\.(?:mp4|mov|m4v|webm)(?:[?#]\\S*)?$", RegexOption.IGNORE_CASE)
private val quote = Regex("^>\\s?(.*)$")
private val check = Regex("^[-*]\\s+\\[([ xX])\\]\\s+(.*)$")
private val bullet = Regex("^[-*]\\s+(.*)$")
private val number = Regex("^\\d+\\.\\s+(.*)$")
private val emphasis = Regex("\\*\\*([^*]+)\\*\\*|\\*([^*]+)\\*")

internal fun parseInline(text: String): List<InlineSpan> {
    val result = mutableListOf<InlineSpan>()
    var last = 0
    for (match in emphasis.findAll(text)) {
        if (match.range.first > last) result += InlineSpan(InlineKind.Text, text.substring(last, match.range.first))
        val bold = match.groups[1]?.value
        result += if (bold != null) InlineSpan(InlineKind.Bold, bold) else InlineSpan(InlineKind.Italic, match.groups[2]!!.value)
        last = match.range.last + 1
    }
    if (last < text.length) result += InlineSpan(InlineKind.Text, text.substring(last))
    return result
}

private enum class ListKind { Bullets, Numbers, Checks }

/** Markdown kecil untuk prosedur yang aturannya sama dengan web (components/markdown/markdown.ts), jadi mengubah satu berarti mengubah keduanya. */
internal fun parseMarkdown(source: String): List<MarkdownBlock> {
    val blocks = mutableListOf<MarkdownBlock>()
    val paragraph = mutableListOf<String>()
    val quoted = mutableListOf<String>()
    var kind: ListKind? = null
    val bullets = mutableListOf<List<InlineSpan>>()
    val numbers = mutableListOf<List<InlineSpan>>()
    val checks = mutableListOf<CheckItem>()

    fun closeList() {
        when (kind) {
            ListKind.Bullets -> blocks += MarkdownBlock.Bullets(bullets.toList())
            ListKind.Numbers -> blocks += MarkdownBlock.Numbers(numbers.toList())
            ListKind.Checks -> blocks += MarkdownBlock.Checks(checks.toList())
            null -> Unit
        }
        bullets.clear()
        numbers.clear()
        checks.clear()
        kind = null
    }

    fun flush() {
        if (paragraph.isNotEmpty()) blocks += MarkdownBlock.Paragraph(parseInline(paragraph.joinToString("\n")))
        if (quoted.isNotEmpty()) blocks += MarkdownBlock.Quote(parseInline(quoted.joinToString("\n")))
        paragraph.clear()
        quoted.clear()
    }

    fun open(next: ListKind) {
        flush()
        if (kind != next) closeList()
        kind = next
    }

    for (raw in source.replace("\r\n", "\n").replace('\r', '\n').split('\n')) {
        val line = raw.trim()
        when {
            line.isEmpty() -> flush()
            heading.matches(line) -> {
                flush(); closeList()
                val found = heading.matchEntire(line)!!
                blocks += MarkdownBlock.Heading(found.groupValues[1].length, parseInline(found.groupValues[2]))
            }
            divider.matches(line) -> {
                flush(); closeList()
                blocks += MarkdownBlock.Divider
            }
            picture.matches(line) -> {
                flush(); closeList()
                val found = picture.matchEntire(line)!!
                val alt = found.groupValues[1]
                val url = found.groupValues[2]
                blocks += if (videoFile.containsMatchIn(url)) MarkdownBlock.Video(alt, url) else MarkdownBlock.Picture(alt, url)
            }
            quote.matches(line) -> {
                if (paragraph.isNotEmpty()) flush()
                closeList()
                quoted += quote.matchEntire(line)!!.groupValues[1]
            }
            check.matches(line) -> {
                open(ListKind.Checks)
                val found = check.matchEntire(line)!!
                checks += CheckItem(found.groupValues[1] != " ", parseInline(found.groupValues[2]))
            }
            bullet.matches(line) -> {
                open(ListKind.Bullets)
                bullets += parseInline(bullet.matchEntire(line)!!.groupValues[1])
            }
            number.matches(line) -> {
                open(ListKind.Numbers)
                numbers += parseInline(number.matchEntire(line)!!.groupValues[1])
            }
            else -> {
                if (quoted.isNotEmpty()) flush()
                closeList()
                paragraph += line
            }
        }
    }
    flush()
    closeList()
    return blocks
}
