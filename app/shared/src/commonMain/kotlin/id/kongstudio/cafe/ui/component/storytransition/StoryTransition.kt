package id.kongstudio.cafe.ui.component.storytransition

import androidx.compose.animation.ContentTransform
import androidx.compose.animation.core.Easing
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.scaleIn
import androidx.compose.animation.scaleOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.animation.slideOutVertically
import androidx.compose.animation.togetherWith
import androidx.compose.ui.unit.IntOffset

/** Peralihan antar halaman cerita; pemutar memilihnya bergiliran supaya tiap halaman terasa berbeda. */
enum class StoryTransitionKind { Push, FadeThrough, Rise, Zoom }

private const val ParallaxDivisor = 3
private const val RiseDivisor = 4
private const val ThroughScale = 0.92f
private const val ZoomFrom = 1.12f
private const val ZoomTo = 0.88f

/** Peralihan [kind]; [forward] menentukan arah gerak, [millis] dan [easing] dari token efek tema. */
fun storyTransition(kind: StoryTransitionKind, forward: Boolean, millis: Int, easing: Easing): ContentTransform {
    val sign = if (forward) 1 else -1
    val move = tween<IntOffset>(millis, easing = easing)
    val fade = tween<Float>(millis, easing = easing)
    val scale = tween<Float>(millis, easing = easing)

    return when (kind) {
        StoryTransitionKind.Push ->
            (slideInHorizontally(move) { it * sign } + fadeIn(fade)) togetherWith
                (slideOutHorizontally(move) { -it * sign / ParallaxDivisor } + fadeOut(fade))

        StoryTransitionKind.FadeThrough ->
            (fadeIn(fade) + scaleIn(scale, initialScale = ThroughScale)) togetherWith
                (fadeOut(fade) + scaleOut(scale, targetScale = ThroughScale))

        StoryTransitionKind.Rise ->
            (slideInVertically(move) { it * sign / RiseDivisor } + fadeIn(fade)) togetherWith
                (slideOutVertically(move) { -it * sign / RiseDivisor } + fadeOut(fade))

        StoryTransitionKind.Zoom ->
            (fadeIn(fade) + scaleIn(scale, initialScale = if (forward) ZoomFrom else ZoomTo)) togetherWith
                (fadeOut(fade) + scaleOut(scale, targetScale = if (forward) ZoomTo else ZoomFrom))
    }
}
