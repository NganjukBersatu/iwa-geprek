package id.kongstudio.cafe.ui.component.expandablecard

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.AnimatedVisibilityScope
import androidx.compose.animation.BoundsTransform
import androidx.compose.animation.EnterExitState
import androidx.compose.animation.ExperimentalSharedTransitionApi
import androidx.compose.animation.SharedTransitionLayout
import androidx.compose.animation.SharedTransitionScope
import androidx.compose.animation.core.animateDp
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.component.backhandler.PlatformBackHandler
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons

/** Radius kartu tertutup; sama dengan AppShapes.card, dibutuhkan sebagai Dp untuk dianimasikan ke nol. */
private val CardRadius = 24.dp
private val SquareCorner = 0.dp
private const val HeadLayer = 1f

/** Isi satu kartu: bagian kepala yang selalu tampak dan [body] yang muncul setelah kartu melebar. */
class ExpandableCardSpec(
    val key: String,
    val containerColor: Color,
    val actionColor: Color,
    val actionTint: Color,
    val openLabel: String,
    val closeLabel: String,
    val head: @Composable ColumnScope.() -> Unit,
    val body: @Composable ColumnScope.() -> Unit,
    val leading: (@Composable () -> Unit)? = null,
    /** Jarak kepala kartu tertutup dari tepi kartu; kosong memakai jarak bawaan. */
    val contentPadding: PaddingValues? = null,
    /** Isi kepala dipusatkan di kartu dan tombol aksi menempel di tepi kanan tanpa menggeser isi. */
    val centered: Boolean = false,
)

private class LastSpec {
    var spec: ExpandableCardSpec? = null
}

/** Wadah kartu yang melebar menjadi layar penuh saat ditekan dan kembali saat ditutup, dengan [content] memanggil [ExpandableCardScope.ExpandableCard] di tempat kartu berada. */
@OptIn(ExperimentalSharedTransitionApi::class)
@Composable
fun ExpandableCardHost(
    expanded: ExpandableCardSpec?,
    onOpen: (ExpandableCardSpec) -> Unit,
    onClose: () -> Unit,
    modifier: Modifier = Modifier,
    content: @Composable ExpandableCardScope.() -> Unit,
) {
    val effects = AppTheme.effects
    val last = remember { LastSpec() }
    if (expanded != null) last.spec = expanded

    PlatformBackHandler(enabled = expanded != null, onBack = onClose)

    SharedTransitionLayout(modifier = modifier) {
        AnimatedContent(
            targetState = expanded?.key,
            transitionSpec = {
                fadeIn(tween(effects.standardMillis)) togetherWith fadeOut(tween(effects.standardMillis))
            },
            label = "expandable-card",
        ) { key ->
            val scope = ExpandableCardScope(this@SharedTransitionLayout, this, onOpen)
            val spec = last.spec
            if (key != null && spec != null) scope.Expanded(spec, onClose) else scope.content()
        }
    }
}

@OptIn(ExperimentalSharedTransitionApi::class)
class ExpandableCardScope internal constructor(
    private val shared: SharedTransitionScope,
    private val visibility: AnimatedVisibilityScope,
    private val onOpen: (ExpandableCardSpec) -> Unit,
) {
    /** Kartu tertutup; menekan seluruh kartu membukanya. */
    @Composable
    fun ExpandableCard(spec: ExpandableCardSpec, modifier: Modifier = Modifier) {
        val spacing = AppTheme.spacing
        val bounds = boundsTransform()

        with(shared) {
            Column(
                modifier = modifier
                    .fillMaxWidth()
                    .sharedBounds(
                        rememberSharedContentState("card-${spec.key}"),
                        visibility,
                        boundsTransform = bounds,
                        resizeMode = SharedTransitionScope.ResizeMode.RemeasureToBounds,
                    )
                    .clip(AppTheme.shapes.card)
                    .background(spec.containerColor)
                    .clickable(onClickLabel = spec.openLabel, role = Role.Button) { onOpen(spec) },
                verticalArrangement = Arrangement.Center,
            ) {
                Head(spec, expanded = false, onAction = null, modifier = Modifier.padding(spec.contentPadding ?: PaddingValues(spacing.lg)))
            }
        }
    }

    /** Kartu terbuka memenuhi area; kepala tetap di tempatnya dan isi muncul di bawahnya. */
    @Composable
    internal fun Expanded(spec: ExpandableCardSpec, onClose: () -> Unit) {
        val spacing = AppTheme.spacing
        val effects = AppTheme.effects
        val bounds = boundsTransform()
        val rise = with(LocalDensity.current) { spacing.lg.roundToPx() }
        val radius by visibility.transition.animateDp(
            transitionSpec = { tween(effects.slowMillis, easing = effects.emphasized) },
            label = "card-corner",
        ) { if (it == EnterExitState.Visible) SquareCorner else CardRadius }
        val bodyEnter = with(visibility) {
            Modifier.animateEnterExit(
                enter = fadeIn(tween(effects.standardMillis, delayMillis = effects.standardMillis)) +
                    slideInVertically(tween(effects.standardMillis, delayMillis = effects.standardMillis)) { rise },
                exit = fadeOut(tween(effects.quickMillis)),
            )
        }

        Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.TopCenter) {
            with(shared) {
                Column(
                    modifier = Modifier
                        .widthIn(max = AppTheme.sizes.contentMaxWidth)
                        .fillMaxHeight()
                        .sharedBounds(
                            rememberSharedContentState("card-${spec.key}"),
                            visibility,
                            boundsTransform = bounds,
                            resizeMode = SharedTransitionScope.ResizeMode.RemeasureToBounds,
                        )
                        .clip(RoundedCornerShape(radius))
                        .background(spec.containerColor),
                ) {
                    Head(spec, expanded = true, onAction = onClose, modifier = Modifier.padding(spacing.lg))
                    Column(
                        modifier = bodyEnter
                            .weight(1f)
                            .fillMaxWidth()
                            .verticalScroll(rememberScrollState())
                            .padding(start = spacing.lg, end = spacing.lg, bottom = spacing.lg),
                        verticalArrangement = Arrangement.spacedBy(spacing.sm),
                    ) { spec.body(this) }
                }
            }
        }
    }

    @Composable
    private fun Head(
        spec: ExpandableCardSpec,
        expanded: Boolean,
        onAction: (() -> Unit)?,
        modifier: Modifier,
    ) {
        val spacing = AppTheme.spacing

        if (spec.centered) {
            Box(modifier = modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                HeadContent(spec, Modifier.fillMaxWidth().padding(horizontal = spacing.touchTarget))
                Box(modifier = Modifier.align(Alignment.CenterEnd)) { Action(spec, expanded, onAction) }
            }
        } else {
            Row(
                modifier = modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(spacing.md),
            ) {
                HeadContent(spec, Modifier.weight(1f))
                Action(spec, expanded, onAction)
            }
        }
    }

    @Composable
    private fun HeadContent(spec: ExpandableCardSpec, modifier: Modifier) {
        val spacing = AppTheme.spacing

        with(shared) {
            Row(
                modifier = modifier.sharedElement(
                    rememberSharedContentState("head-${spec.key}"),
                    visibility,
                    zIndexInOverlay = HeadLayer,
                ),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(spacing.md),
            ) {
                spec.leading?.invoke()
                Column(modifier = Modifier.weight(1f)) { spec.head(this) }
            }
        }
    }

    @Composable
    private fun Action(spec: ExpandableCardSpec, expanded: Boolean, onClick: (() -> Unit)?) {
        val effects = AppTheme.effects
        val fade = with(visibility) {
            Modifier.animateEnterExit(
                enter = fadeIn(tween(effects.standardMillis, delayMillis = if (expanded) effects.standardMillis else 0)),
                exit = fadeOut(tween(effects.quickMillis)),
            )
        }
        val press = if (onClick != null) {
            Modifier
                .semantics { contentDescription = spec.closeLabel }
                .clickable(role = Role.Button, onClick = onClick)
        } else {
            Modifier
        }

        Box(
            modifier = fade.size(AppTheme.spacing.touchTarget).then(press),
            contentAlignment = Alignment.Center,
        ) {
            Box(
                modifier = Modifier
                    .size(AppTheme.sizes.controlSmall)
                    .clip(AppTheme.shapes.pill)
                    .background(spec.actionColor),
                contentAlignment = Alignment.Center,
            ) {
                AppIcon(
                    icon = if (expanded) AppIcons.Close else AppIcons.ChevronRight,
                    tint = spec.actionTint,
                    size = AppTheme.sizes.iconSmall,
                )
            }
        }
    }

    @Composable
    private fun boundsTransform(): BoundsTransform {
        val effects = AppTheme.effects
        return remember(effects) {
            BoundsTransform { _, _ -> tween(durationMillis = effects.slowMillis, easing = effects.emphasized) }
        }
    }
}
