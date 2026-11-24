package id.kongstudio.cafe.ui.component.systemtimepicker

import android.app.TimePickerDialog
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.platform.LocalContext

@Composable
actual fun SystemTimePicker(initial: String, onPicked: (String) -> Unit, onDismiss: () -> Unit) {
    val context = LocalContext.current
    val picked = rememberUpdatedState(onPicked)
    val dismissed = rememberUpdatedState(onDismiss)

    DisposableEffect(Unit) {
        val hour = initial.substringBefore(':').toIntOrNull() ?: 0
        val minute = initial.substringAfter(':', "0").toIntOrNull() ?: 0
        val dialog = TimePickerDialog(
            context,
            { _, selectedHour, selectedMinute ->
                picked.value("${selectedHour.toString().padStart(2, '0')}:${selectedMinute.toString().padStart(2, '0')}")
            },
            hour,
            minute,
            true,
        )
        dialog.setOnDismissListener { dismissed.value() }
        dialog.show()
        onDispose {
            dialog.setOnDismissListener(null)
            dialog.dismiss()
        }
    }
}
