package id.kongstudio.cafe.feature.performance

import androidx.compose.runtime.Composable
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.performance_rating_attendance
import id.kongstudio.cafe.resources.performance_rating_group_behavior
import id.kongstudio.cafe.resources.performance_rating_group_work
import id.kongstudio.cafe.resources.performance_rating_given_tasks_done
import id.kongstudio.cafe.resources.performance_rating_given_tasks_in_time
import id.kongstudio.cafe.resources.performance_rating_own_tasks_done
import id.kongstudio.cafe.resources.performance_rating_own_tasks_in_time
import id.kongstudio.cafe.resources.performance_slice_on_time
import org.jetbrains.compose.resources.stringResource
import kotlin.math.roundToInt

private const val NO_VALUE = "—"
private const val TENTHS = 10

@Composable
internal fun RatingGroup.label(): String = when (key) {
    "behavior" -> stringResource(Res.string.performance_rating_group_behavior)
    "work" -> stringResource(Res.string.performance_rating_group_work)
    else -> key
}

@Composable
internal fun RatingComponent.label(): String = when (key) {
    "on_time" -> stringResource(Res.string.performance_slice_on_time)
    "attendance" -> stringResource(Res.string.performance_rating_attendance)
    "given_tasks_done" -> stringResource(Res.string.performance_rating_given_tasks_done)
    "given_tasks_in_time" -> stringResource(Res.string.performance_rating_given_tasks_in_time)
    "own_tasks_done" -> stringResource(Res.string.performance_rating_own_tasks_done)
    "own_tasks_in_time" -> stringResource(Res.string.performance_rating_own_tasks_in_time)
    else -> key
}

internal fun RatingComponent.valueText(): String = percent?.let { "${it.roundToInt()}%" } ?: NO_VALUE

/** Bintang dengan satu angka di belakang koma memakai koma, misalnya 4,5. */
internal fun Double.starsText(): String {
    val tenths = (this * TENTHS).roundToInt()
    return "${tenths / TENTHS},${tenths % TENTHS}"
}
