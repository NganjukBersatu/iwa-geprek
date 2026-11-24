package id.kongstudio.cafe.ui.component.systemtimepicker

import androidx.compose.runtime.Composable

/** Pemilih jam bawaan sistem berformat 24 jam; [initial] dan hasil [onPicked] berbentuk "HH:MM", dan [onDismiss] dipanggil setiap kali dialog tertutup. */
@Composable
expect fun SystemTimePicker(initial: String, onPicked: (String) -> Unit, onDismiss: () -> Unit)
