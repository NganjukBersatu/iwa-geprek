package id.kongstudio.cafe.ui.component.datefield

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.Role
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.format.longDateLabel
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.format_month_year
import id.kongstudio.cafe.resources.months
import id.kongstudio.cafe.resources.weekdays_short
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.monthcalendar.MonthCalendar
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringArrayResource
import org.jetbrains.compose.resources.stringResource
import id.kongstudio.cafe.ui.component.appicon.AppIcon

/** Isian tanggal berformat "YYYY-MM-DD" yang tampil seperti kolom teks dan membuka kalender bulan di lembar bawah saat diketuk; nilai kosong menampilkan [placeholder]. */
@Composable
internal fun DateField(
    label: String,
    value: String,
    today: String,
    onValueChange: (String) -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    placeholder: String? = null,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val shape = AppTheme.shapes.field
    val months = stringArrayResource(Res.array.months)
    var open by remember { mutableStateOf(false) }
    var month by remember(value) { mutableStateOf(DateTimeFormat.monthOf(value.ifEmpty { today })) }

    Column(modifier) {
        BasicText(text = label, style = AppTheme.typography.label.copy(color = colors.content))
        Row(
            modifier = Modifier
                .padding(top = spacing.xs)
                .fillMaxWidth()
                .heightIn(min = spacing.touchTarget)
                .clip(shape)
                .background(colors.surface)
                .border(AppTheme.sizes.borderField, colors.outline, shape)
                .clickable(enabled = enabled, role = Role.Button) { open = true }
                .padding(horizontal = spacing.md),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(spacing.sm),
        ) {
            BasicText(
                text = if (value.isEmpty()) placeholder.orEmpty() else longDateLabel(value),
                style = AppTheme.typography.body.copy(color = if (value.isEmpty()) colors.contentMuted else colors.content),
                modifier = Modifier.weight(1f),
            )
            AppIcon(icon = AppIcons.Calendar, tint = colors.primary, size = AppTheme.sizes.icon)
        }
    }

    if (open) {
        AppBottomSheet(title = label, onDismiss = { open = false }) {
            MonthCalendar(
                month = month,
                monthLabel = stringResource(
                    Res.string.format_month_year,
                    months[month.month - 1],
                    month.year.toString(),
                ),
                weekdayLabels = stringArrayResource(Res.array.weekdays_short),
                selected = value,
                today = today,
                markers = emptyMap(),
                fills = emptyMap(),
                onSelect = { date ->
                    onValueChange(date)
                    open = false
                },
                onPrevious = { month = month.previous() },
                onNext = { month = month.next() },
                nextEnabled = true,
            )
        }
    }
}
