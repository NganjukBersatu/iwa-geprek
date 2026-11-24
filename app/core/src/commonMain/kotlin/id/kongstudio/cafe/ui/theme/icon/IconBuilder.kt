package id.kongstudio.cafe.ui.theme.icon

import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.vector.PathParser
import androidx.compose.ui.unit.dp

private const val Grid = 24f

/** Membangun ikon garis (viewBox 24, stroke 2, ujung bulat) dari data path SVG milik pack ikon. */
internal fun strokeIcon(name: String, vararg paths: String): ImageVector =
    ImageVector.Builder(
        name = name,
        defaultWidth = Grid.dp,
        defaultHeight = Grid.dp,
        viewportWidth = Grid,
        viewportHeight = Grid,
    ).apply {
        paths.forEach { d ->
            addPath(
                pathData = PathParser().parsePathString(d).toNodes(),
                stroke = SolidColor(Color.Black),
                strokeLineWidth = 2f,
                strokeLineCap = StrokeCap.Round,
                strokeLineJoin = StrokeJoin.Round,
            )
        }
    }.build()

/** Membangun ikon terisi (viewBox 24) dari data path SVG milik set filled pack ikon. */
internal fun filledIcon(name: String, vararg paths: String): ImageVector =
    ImageVector.Builder(
        name = name,
        defaultWidth = Grid.dp,
        defaultHeight = Grid.dp,
        viewportWidth = Grid,
        viewportHeight = Grid,
    ).apply {
        paths.forEach { d ->
            addPath(pathData = PathParser().parsePathString(d).toNodes(), fill = SolidColor(Color.Black))
        }
    }.build()
