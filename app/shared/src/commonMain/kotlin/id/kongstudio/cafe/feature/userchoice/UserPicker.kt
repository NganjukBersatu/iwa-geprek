package id.kongstudio.cafe.feature.userchoice

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.rememberScrollState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.feature.admin.ListParam
import id.kongstudio.cafe.feature.admin.PagedListViewModel
import id.kongstudio.cafe.feature.admin.rememberChoicePages
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.common_all
import id.kongstudio.cafe.resources.user_choice_empty
import id.kongstudio.cafe.resources.user_choice_inactive
import id.kongstudio.cafe.resources.user_choice_search
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.resourcelist.ResourcePicker
import id.kongstudio.cafe.ui.component.scrollend.OnScrollEnd
import id.kongstudio.cafe.ui.component.skeleton.SkeletonRows
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

private const val SearchSkeletonRows = 4
private const val MoreSkeletonRows = 2

/** Memilih satu orang dengan pencarian nama; baris "Semua" di atas melepas pilihan. */
@Composable
internal fun UserPicker(title: String, repository: UserChoiceRepository, onPicked: (UserChoice?) -> Unit, onDismiss: () -> Unit) {
    var query by remember { mutableStateOf("") }
    val choices = rememberChoicePages<UserChoice>(key = { it.id }, fetch = repository::choices)
    val scroll = rememberScrollState()
    OnScrollEnd(scroll = scroll, count = choices.items.size, onEnd = choices::more)

    AppBottomSheet(title = title, onDismiss = onDismiss, scroll = scroll, busy = choices.busy) {
        Column(verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md)) {
            AppTextField(
                value = query,
                onValueChange = {
                    query = it
                    choices.search(it)
                },
                label = stringResource(Res.string.user_choice_search),
            )
            choices.failure?.let { InlineMessage(text = failureText(it)) }
            if (query.isBlank()) ListRow(title = stringResource(Res.string.common_all), onClick = { onPicked(null) })
            if (choices.searching) {
                SkeletonRows(count = SearchSkeletonRows)
                return@Column
            }
            if (choices.failure == null && choices.items.isEmpty()) {
                AppText(text = stringResource(Res.string.user_choice_empty), role = TextRole.Caption, color = AppTheme.colors.contentMuted)
            }
            val inactive = stringResource(Res.string.user_choice_inactive)
            choices.items.forEach { person ->
                ListRow(
                    title = person.name,
                    detail = listOfNotNull(person.outletName, inactive.takeIf { !person.active }).joinToString(" · ").ifEmpty { null },
                    onClick = { onPicked(person) },
                )
            }
            if (choices.loadingMore) SkeletonRows(count = MoreSkeletonRows)
        }
    }
}

/**
 * Penyaring "Dicatat oleh" sebuah daftar: pilihannya disimpan di [list] lewat [ListParam.UserId] (dikirim ke server)
 * dan [ListParam.UserName] (hanya untuk label), dan lembar pilihnya muncul di atas lembar Filter.
 */
@Composable
internal fun userFilter(list: PagedListViewModel<*>, label: String, repository: UserChoiceRepository): ResourcePicker {
    var picking by remember { mutableStateOf(false) }
    val state by list.state.collectAsState()
    val params = state.params
    if (picking) {
        UserPicker(
            title = label,
            repository = repository,
            onPicked = { person ->
                picking = false
                list.setParams(ListParam.UserId to person?.id.orEmpty(), ListParam.UserName to person?.name.orEmpty())
            },
            onDismiss = { picking = false },
        )
    }
    return ResourcePicker(
        label = label,
        selectedLabel = params[ListParam.UserName]?.takeIf { params[ListParam.UserId].orEmpty().isNotEmpty() },
        allLabel = stringResource(Res.string.common_all),
        onOpen = { picking = true },
        onClear = { list.setParams(ListParam.UserId to "", ListParam.UserName to "") },
    )
}
