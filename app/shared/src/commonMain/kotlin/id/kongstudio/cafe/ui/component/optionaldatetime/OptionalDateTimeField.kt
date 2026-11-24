package id.kongstudio.cafe.ui.component.optionaldatetime

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.time.ServerClock
import id.kongstudio.cafe.ui.component.datefield.DateField
import id.kongstudio.cafe.ui.component.timefield.TimeField
import id.kongstudio.cafe.ui.component.toggleswitch.ToggleSwitch
import id.kongstudio.cafe.ui.theme.AppTheme

private const val DefaultLeadSeconds = 3_600L

/** Tanggal dan jam waktu setempat; [toIso] memberi bentuk yang dikirim ke server. */
class DateTimeValue(val date: String, val time: String) {
    fun toIso() = DateTimeFormat.wibIso(date, time)
}

/** Isian tanggal dan jam yang boleh dikosongkan lewat saklar, kecuali [removable] false dan nilainya sudah ada. */
@Composable
internal fun OptionalDateTimeField(
    toggleLabel: String,
    dateLabel: String,
    timeLabel: String,
    value: DateTimeValue?,
    onChange: (DateTimeValue?) -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    removable: Boolean = true,
) {
    val today = remember { DateTimeFormat.todayWib() }

    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md)) {
        if (removable || value == null) {
            ToggleSwitch(
                label = toggleLabel,
                checked = value != null,
                onCheckedChange = { on ->
                    if (!enabled) return@ToggleSwitch
                    onChange(if (on) defaultValue() else null)
                },
            )
        }
        if (value != null) {
            DateField(
                label = dateLabel,
                value = value.date,
                today = today,
                enabled = enabled,
                onValueChange = { onChange(DateTimeValue(it, value.time)) },
            )
            TimeField(
                label = timeLabel,
                value = value.time,
                enabled = enabled,
                onValueChange = { onChange(DateTimeValue(value.date, it)) },
            )
        }
    }
}

private fun defaultValue(): DateTimeValue {
    val stamp = DateTimeFormat.stampAt(ServerClock.nowEpochSeconds() + DefaultLeadSeconds)
    return DateTimeValue(stamp.date, stamp.time)
}
