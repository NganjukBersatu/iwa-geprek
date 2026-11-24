package id.kongstudio.cafe.ui.component.productcard

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.quantity_increase
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.component.quantitystepper.QuantityStepper
import id.kongstudio.cafe.ui.component.remoteimage.RemoteImageFill
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

private val TileHeight = 96.dp

/** Kartu menu di kasir yang menambah satu saat diketuk, dengan [unavailableLabel] terisi berarti tidak bisa dipesan dan [unavailableTone] menentukan warnanya, [stepper] dimatikan untuk menu berpilihan, dan [tag] penanda kecil seperti promo; tingginya sama untuk semua kartu supaya baris kisi rata. */
@Composable
fun ProductCard(
    name: String,
    price: String,
    quantity: Int,
    onAdd: () -> Unit,
    onDecrease: () -> Unit,
    modifier: Modifier = Modifier,
    imageUrl: String? = null,
    unavailableLabel: String? = null,
    unavailableTone: BlockedTone = BlockedTone.Danger,
    stepper: Boolean = true,
    tag: String? = null,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val shape = AppTheme.shapes.field
    val ordered = quantity > 0
    val blocked = unavailableLabel != null
    // Tinggi mengikuti skala huruf perangkat: dua baris nama dan satu baris harga selalu muat.
    val bodyLine = AppTheme.typography.body.lineHeight
    val labelLine = AppTheme.typography.label.lineHeight
    val textBlock = with(LocalDensity.current) { bodyLine.toDp() * 2 + labelLine.toDp() }
    val cardHeight = TileHeight + textBlock + spacing.sm + spacing.xs + spacing.lg + AppTheme.sizes.borderThick

    Column(
        modifier = modifier
            .fillMaxWidth()
            .height(cardHeight)
            .clip(shape)
            .background(colors.surface)
            .border(
                if (ordered) AppTheme.sizes.borderThick else AppTheme.sizes.borderThin,
                if (ordered) colors.primary else colors.divider,
                shape,
            )
            .clickable(enabled = !blocked, role = Role.Button, onClick = onAdd),
    ) {
        Box(modifier = Modifier.fillMaxWidth().height(TileHeight)) {
            Box(modifier = Modifier.matchParentSize().alpha(if (blocked) DimmedAlpha else 1f)) {
                if (imageUrl != null) {
                    RemoteImageFill(url = imageUrl, contentDescription = name)
                } else {
                    InitialTile(name = name)
                }
            }
            tag?.let { PillLabel(text = it, container = colors.caution, content = colors.content, modifier = Modifier.align(Alignment.TopStart).padding(spacing.xs)) }
            if (blocked) {
                BlockedLabel(text = unavailableLabel.orEmpty(), tone = unavailableTone, modifier = Modifier.align(Alignment.Center))
            } else {
                OrderControl(
                    quantity = quantity,
                    stepper = stepper,
                    onAdd = onAdd,
                    onDecrease = onDecrease,
                    modifier = Modifier.align(Alignment.BottomEnd).padding(spacing.xs),
                )
            }
        }
        Column(
            modifier = Modifier.padding(start = spacing.sm, end = spacing.sm, top = spacing.sm, bottom = spacing.md),
            verticalArrangement = Arrangement.spacedBy(spacing.xs),
        ) {
            BasicText(
                text = name,
                style = AppTheme.typography.body.copy(color = if (blocked) colors.contentMuted else colors.content),
                minLines = 2,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
            BasicText(
                text = price,
                style = AppTheme.typography.label.copy(color = colors.contentMuted),
                maxLines = 1,
            )
        }
    }
}

/** Tombol tambah atau pengatur jumlah di sudut ubin; berlatar permukaan supaya terbaca di atas foto. */
@Composable
private fun OrderControl(quantity: Int, stepper: Boolean, onAdd: () -> Unit, onDecrease: () -> Unit, modifier: Modifier = Modifier) {
    val colors = AppTheme.colors
    val ordered = quantity > 0
    if (ordered && stepper) {
        Box(modifier = modifier.clip(AppTheme.shapes.pill).background(colors.surface)) {
            QuantityStepper(quantity = quantity, onDecrease = onDecrease, onIncrease = onAdd)
        }
        return
    }
    Box(
        modifier = modifier
            .size(AppTheme.sizes.control)
            .clip(AppTheme.shapes.pill)
            .background(colors.primary),
        contentAlignment = Alignment.Center,
    ) {
        if (ordered) {
            BasicText(text = quantity.toString(), style = AppTheme.typography.button.copy(color = colors.onPrimary))
        } else {
            AppIcon(icon = AppIcons.Plus, tint = colors.onPrimary, size = AppTheme.sizes.iconSmall, contentDescription = stringResource(Res.string.quantity_increase))
        }
    }
}

/** Pengganti foto untuk menu tanpa gambar: huruf awal nama di atas latar aksen muda, di bagian atas supaya pengatur jumlah di sudut bawah tidak menutupinya. */
@Composable
private fun InitialTile(name: String) {
    val colors = AppTheme.colors
    Box(modifier = Modifier.fillMaxSize().background(colors.accentSurface).padding(top = AppTheme.spacing.sm), contentAlignment = Alignment.TopCenter) {
        BasicText(
            text = name.trim().take(1).uppercase(),
            style = AppTheme.typography.headline.copy(color = colors.content),
        )
    }
}

private val DimmedAlpha = 0.45f
