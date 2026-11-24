package id.kongstudio.cafe.ui.component.markdown

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.markdown_video_hint
import id.kongstudio.cafe.resources.markdown_video_play
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.remoteimage.RemoteImage
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

private val CheckBoxSize = 20.dp
private val CheckMarkSize = 14.dp
private val QuoteBarWidth = 4.dp
private val CheckBoxRadius = 6.dp
private val H2Size = 20.sp
private val H2Line = 26.sp

/** Isi slide ditulis dalam Markdown kecil ([parseMarkdown]); menggambar judul, paragraf, daftar, kutipan, garis, gambar, dan video. */
@Composable
fun MarkdownContent(source: String, modifier: Modifier = Modifier) {
    val blocks = remember(source) { parseMarkdown(source) }
    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md)) {
        blocks.forEach { Block(it) }
    }
}

@Composable
private fun Block(block: MarkdownBlock) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val typography = AppTheme.typography
    val body = typography.body.copy(color = colors.content)

    when (block) {
        is MarkdownBlock.Heading -> {
            val style = when (block.level) {
                1 -> typography.title
                2 -> typography.title.copy(fontSize = H2Size, lineHeight = H2Line)
                else -> typography.button
            }
            BasicText(text = styled(block.spans), style = style.copy(color = colors.content))
        }
        is MarkdownBlock.Paragraph -> BasicText(text = styled(block.spans), style = body)
        is MarkdownBlock.Bullets -> Column(verticalArrangement = Arrangement.spacedBy(spacing.xs)) {
            block.items.forEach { Item(marker = "•", spans = it, style = body) }
        }
        is MarkdownBlock.Numbers -> Column(verticalArrangement = Arrangement.spacedBy(spacing.xs)) {
            block.items.forEachIndexed { index, spans -> Item(marker = "${index + 1}.", spans = spans, style = body) }
        }
        is MarkdownBlock.Checks -> Column(verticalArrangement = Arrangement.spacedBy(spacing.sm)) {
            block.items.forEach { Check(it, body) }
        }
        is MarkdownBlock.Quote -> Row(
            modifier = Modifier
                .fillMaxWidth()
                .height(IntrinsicSize.Min)
                .clip(AppTheme.shapes.field)
                .background(colors.selected),
        ) {
            Box(modifier = Modifier.width(QuoteBarWidth).fillMaxHeight().background(colors.primary))
            BasicText(text = styled(block.spans), style = body, modifier = Modifier.padding(spacing.md))
        }
        MarkdownBlock.Divider -> Box(modifier = Modifier.fillMaxWidth().height(AppTheme.sizes.borderThin).background(colors.divider))
        is MarkdownBlock.Picture -> RemoteImage(url = block.url, contentDescription = block.alt.ifBlank { null }, fit = true)
        is MarkdownBlock.Video -> VideoBlock(block)
    }
}

/** Video tetap di posisinya di dalam slide; diketuk untuk diputar di pemutar video perangkat. */
@Composable
private fun VideoBlock(block: MarkdownBlock.Video) {
    val uriHandler = LocalUriHandler.current
    ListCard {
        ListRow(
            title = block.alt.ifBlank { stringResource(Res.string.markdown_video_play) },
            caption = stringResource(Res.string.markdown_video_hint),
            leading = { IconBadge(AppIcons.Video) },
            trailing = { AppIcon(icon = AppIcons.ChevronRight, tint = AppTheme.colors.contentMuted) },
            onClick = { uriHandler.openUri(block.url) },
        )
    }
}

@Composable
private fun Item(marker: String, spans: List<InlineSpan>, style: TextStyle) {
    Row(horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm)) {
        BasicText(text = marker, style = style)
        BasicText(text = styled(spans), style = style, modifier = Modifier.weight(1f))
    }
}

@Composable
private fun Check(item: CheckItem, style: TextStyle) {
    val colors = AppTheme.colors
    Row(horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm), verticalAlignment = Alignment.Top) {
        Box(
            modifier = Modifier
                .size(CheckBoxSize)
                .clip(RoundedCornerShape(CheckBoxRadius))
                .background(if (item.checked) colors.primary else colors.surface)
                .border(AppTheme.sizes.borderThin, if (item.checked) colors.primary else colors.outline, RoundedCornerShape(CheckBoxRadius)),
            contentAlignment = Alignment.Center,
        ) {
            if (item.checked) AppIcon(icon = AppIcons.Check, tint = colors.onPrimary, size = CheckMarkSize)
        }
        BasicText(
            text = styled(item.spans),
            style = if (item.checked) style.copy(color = colors.contentMuted, textDecoration = TextDecoration.LineThrough) else style,
            modifier = Modifier.weight(1f),
        )
    }
}

private fun styled(spans: List<InlineSpan>): AnnotatedString = buildAnnotatedString {
    spans.forEach { span ->
        when (span.kind) {
            InlineKind.Text -> append(span.text)
            InlineKind.Bold -> withStyle(SpanStyle(fontWeight = FontWeight.Bold)) { append(span.text) }
            InlineKind.Italic -> withStyle(SpanStyle(fontStyle = FontStyle.Italic)) { append(span.text) }
        }
    }
}
