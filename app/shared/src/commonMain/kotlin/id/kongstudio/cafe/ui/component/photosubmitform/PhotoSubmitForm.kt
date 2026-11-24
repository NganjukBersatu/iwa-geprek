package id.kongstudio.cafe.ui.component.photosubmitform

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.photofield.PhotoField
import id.kongstudio.cafe.ui.component.photopicker.PickedPhoto
import id.kongstudio.cafe.ui.theme.AppTheme

/** Formulir pengiriman berfoto yang seragam, dengan [photoRequired] true tombol aktif setelah foto dipilih dan bila false [onSubmit] menerima null; [allowGallery] false memaksa foto dari kamera. */
@Composable
fun PhotoSubmitForm(
    submitLabel: String,
    onSubmit: (photo: ByteArray?) -> Unit,
    modifier: Modifier = Modifier,
    submitting: Boolean = false,
    canSubmit: Boolean = true,
    photoRequired: Boolean = true,
    allowGallery: Boolean = true,
    error: String? = null,
    fields: @Composable ColumnScope.() -> Unit = {},
) {
    var photo by remember { mutableStateOf<PickedPhoto?>(null) }

    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md),
    ) {
        fields()
        PhotoField(photo = photo, onPicked = { photo = it }, enabled = !submitting, allowGallery = allowGallery)
        error?.let { InlineMessage(text = it) }
        PrimaryButton(
            text = submitLabel,
            onClick = { onSubmit(photo?.bytes) },
            enabled = (photo != null || !photoRequired) && canSubmit && !submitting,
            loading = submitting,
        )
    }
}
