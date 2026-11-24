package id.kongstudio.cafe.feature.about

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.style.TextAlign
import id.kongstudio.cafe.feature.release.ApkReleaseNotes
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.about_developer_line
import id.kongstudio.cafe.resources.about_place
import id.kongstudio.cafe.resources.about_purpose
import id.kongstudio.cafe.resources.about_purpose_title
import id.kongstudio.cafe.resources.about_thanks
import id.kongstudio.cafe.resources.about_thanks_title
import id.kongstudio.cafe.resources.about_version_line
import id.kongstudio.cafe.resources.brand_logo
import id.kongstudio.cafe.resources.release_title
import id.kongstudio.cafe.resources.splash_app_name
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.divider.AppDivider
import id.kongstudio.cafe.ui.component.divideditems.DividedItems
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.pageframe.PageFrame
import id.kongstudio.cafe.ui.component.pagetitle.PageTitle
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.painterResource
import org.jetbrains.compose.resources.stringResource

/** Halaman Info Aplikasi: identitas dan versi, isi "Yang baru" versi terpasang, tujuan aplikasi, dan ucapan terima kasih; [title] diisi bila halaman tidak dibingkai judul dari luar. */
@Composable
internal fun AboutPage(modifier: Modifier = Modifier, title: String? = null) {
    val spacing = AppTheme.spacing
    PageFrame(modifier = modifier) {
        if (title != null) {
            item { PageTitle(title = title) }
        }
        item {
            // Satu kolom di semua ukuran layar, supaya urutan bacanya sama di HP dan tablet.
            Column(verticalArrangement = Arrangement.spacedBy(spacing.md)) {
                IdentityCard()
                ReleaseCard()
                TextCard(icon = AppIcons.Info, title = stringResource(Res.string.about_purpose_title), text = stringResource(Res.string.about_purpose))
                TextCard(icon = AppIcons.HeartHandshake, title = stringResource(Res.string.about_thanks_title), text = stringResource(Res.string.about_thanks))
                DeveloperLine()
            }
        }
    }
}

@Composable
private fun IdentityCard() {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val shape = AppTheme.shapes.field
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(shape)
            .background(colors.primary)
            .padding(horizontal = spacing.lg, vertical = spacing.xl),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(spacing.md),
    ) {
        Image(
            painter = painterResource(Res.drawable.brand_logo),
            contentDescription = null,
            contentScale = ContentScale.Fit,
            modifier = Modifier.size(AppTheme.sizes.avatarLarge).clip(shape),
        )
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            AppText(text = stringResource(Res.string.splash_app_name), role = TextRole.Headline, color = colors.onPrimary, textAlign = TextAlign.Center)
            AppText(text = stringResource(Res.string.about_place), role = TextRole.Body, color = colors.onPrimaryMuted, textAlign = TextAlign.Center)
        }
        Row(
            modifier = Modifier
                .clip(AppTheme.shapes.pill)
                .background(colors.onPrimarySubtle)
                .padding(horizontal = spacing.md, vertical = spacing.xs),
            horizontalArrangement = Arrangement.spacedBy(spacing.xs),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            AppIcon(icon = AppIcons.Apps, tint = colors.onPrimary, size = AppTheme.sizes.iconSmall)
            AppText(text = stringResource(Res.string.about_version_line, appVersionLabel()), role = TextRole.Label, color = colors.onPrimary)
        }
    }
}

@Composable
private fun ReleaseCard() {
    ListCard {
        CardHeader(icon = AppIcons.Sparkles, title = stringResource(Res.string.release_title, appVersionName()))
        AppDivider()
        DividedItems(ApkReleaseNotes) { (text, icon) ->
            ListRow(title = stringResource(text), leading = { IconBadge(icon = icon) })
        }
    }
}

@Composable
private fun TextCard(icon: ImageVector, title: String, text: String) {
    ListCard {
        CardHeader(icon = icon, title = title)
        AppDivider()
        AppText(text = text, modifier = Modifier.padding(AppTheme.spacing.lg))
    }
}

@Composable
private fun CardHeader(icon: ImageVector, title: String) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(AppTheme.spacing.md),
        horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.md),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        IconBadge(icon = icon)
        AppText(text = title, role = TextRole.Title)
    }
}

@Composable
private fun DeveloperLine() {
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = AppTheme.spacing.sm),
        horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.xs, Alignment.CenterHorizontally),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        AppIcon(icon = AppIcons.Code, tint = AppTheme.colors.contentMuted, size = AppTheme.sizes.iconSmall)
        AppText(text = stringResource(Res.string.about_developer_line), role = TextRole.Caption, color = AppTheme.colors.contentMuted)
    }
}
