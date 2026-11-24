package id.kongstudio.cafe.core.text

import androidx.compose.runtime.Composable
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.failure.failureText
import org.jetbrains.compose.resources.StringResource
import org.jetbrains.compose.resources.stringResource

/** Teks tampilan yang dibawa lapisan data dan baru diterjemahkan ke string di layar. */
sealed interface UiText {
    data class Plain(val value: String) : UiText

    class Resource(val resource: StringResource, vararg val args: Any) : UiText

    /** Galat jaringan atau server; teksnya selalu dari [failureText]. */
    data class Failed(val failure: AppFailure) : UiText
}

@Composable
fun UiText.resolve(): String = when (this) {
    is UiText.Plain -> value
    is UiText.Resource -> stringResource(resource, *args)
    is UiText.Failed -> failureText(failure)
}
