package id.kongstudio.cafe.feature.cashier.cart

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.feature.cashier.CustomerSuggestion
import id.kongstudio.cafe.feature.cashier.OrderNote
import id.kongstudio.cafe.feature.cashier.VisitorChoices
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.cashier_customer
import id.kongstudio.cafe.resources.cashier_customer_linked
import id.kongstudio.cafe.resources.cashier_customer_visits
import id.kongstudio.cafe.resources.cashier_dine_in
import id.kongstudio.cafe.resources.cashier_not_filled
import id.kongstudio.cafe.resources.cashier_order_note
import id.kongstudio.cafe.resources.cashier_order_note_add
import id.kongstudio.cafe.resources.cashier_order_note_empty
import id.kongstudio.cafe.resources.cashier_order_note_search
import id.kongstudio.cafe.resources.cashier_order_type
import id.kongstudio.cafe.resources.cashier_table
import id.kongstudio.cafe.resources.cashier_take_away
import id.kongstudio.cafe.resources.cashier_visitor_category
import id.kongstudio.cafe.resources.cashier_visitor_gender
import id.kongstudio.cafe.ui.component.choicegroup.ChoiceGroup
import id.kongstudio.cafe.ui.component.dropdownfield.DropdownField
import id.kongstudio.cafe.ui.component.dropdownfield.DropdownOption
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.suggestionfield.Suggestion
import id.kongstudio.cafe.ui.component.suggestionfield.SuggestionField
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.focus.FocusDirection
import androidx.compose.foundation.text.KeyboardActions

// Sama dengan batas nama catatan pesanan di server, supaya catatan baru tidak ditolak karena terlalu panjang.
private const val OrderNoteMaxLength = 100

/** Isian identitas satu pesanan; semuanya opsional kecuali jenis pesanan. */
internal class OrderIdentity(
    val takeAway: Boolean,
    val customerName: String,
    val customerLinked: Boolean,
    val customerSuggestions: List<CustomerSuggestion>,
    val suggestionFailure: AppFailure?,
    val tableNo: String,
    val visitors: VisitorChoices,
    val visitorCategoryId: String?,
    val visitorGenderId: String?,
    val notes: List<OrderNote>,
    val noteId: String?,
    val noteFailure: AppFailure?,
)

internal class OrderIdentityActions(
    val onTakeAway: (Boolean) -> Unit,
    val onCustomerName: (String) -> Unit,
    val onPickCustomer: (CustomerSuggestion) -> Unit,
    val onTableNo: (String) -> Unit,
    val onVisitorCategory: (String?) -> Unit,
    val onVisitorGender: (String?) -> Unit,
    val onNote: (String?) -> Unit,
    val onAddNote: (String) -> Unit,
)

/** Identitas pesanan dengan urutan yang sama seperti kasir web: jenis, pelanggan, meja, pengunjung, lalu catatan. */
@Composable
internal fun OrderTypeField(
    identity: OrderIdentity,
    actions: OrderIdentityActions,
    modifier: Modifier = Modifier,
) {
    ChoiceGroup(
        label = stringResource(Res.string.cashier_order_type),
        options = listOf(
            stringResource(Res.string.cashier_dine_in),
            stringResource(Res.string.cashier_take_away),
        ),
        icons = listOf(AppIcons.Armchair, AppIcons.ShoppingBag),
        selectedIndex = if (identity.takeAway) 1 else 0,
        onSelect = { actions.onTakeAway(it == 1) },
        modifier = modifier,
    )
}

@Composable
internal fun OrderHeader(
    identity: OrderIdentity,
    actions: OrderIdentityActions,
    modifier: Modifier = Modifier,
) {
    val notFilled = stringResource(Res.string.cashier_not_filled)
    val focus = LocalFocusManager.current
    val category = identity.visitors.categories.firstOrNull { it.id == identity.visitorCategoryId }

    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md),
    ) {
        CustomerField(identity, actions)
        AppTextField(
            value = identity.tableNo,
            onValueChange = actions.onTableNo,
            label = stringResource(Res.string.cashier_table),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number, imeAction = ImeAction.Done),
            keyboardActions = KeyboardActions(onDone = { focus.clearFocus() }),
        )
        if (identity.visitors.categories.isNotEmpty()) {
            DropdownField(
                label = stringResource(Res.string.cashier_visitor_category),
                options = listOf(DropdownOption(null, notFilled)) +
                    identity.visitors.categories.map { DropdownOption(it.id, it.name) },
                selectedKey = identity.visitorCategoryId,
                onSelect = actions.onVisitorCategory,
            )
        }
        if (category?.asksGender == true && identity.visitors.genders.isNotEmpty()) {
            DropdownField(
                label = stringResource(Res.string.cashier_visitor_gender),
                options = listOf(DropdownOption(null, notFilled)) +
                    identity.visitors.genders.map { DropdownOption(it.id, it.name) },
                selectedKey = identity.visitorGenderId,
                onSelect = actions.onVisitorGender,
            )
        }
        NoteField(identity, actions, notFilled)
    }
}

@Composable
private fun CustomerField(identity: OrderIdentity, actions: OrderIdentityActions) {
    val visits = Res.string.cashier_customer_visits
    val focus = LocalFocusManager.current
    val suggestions = identity.customerSuggestions.map { customer ->
        Suggestion(key = customer.id, title = customer.name, subtitle = customer.contact, trailing = stringResource(visits, customer.visits))
    }
    SuggestionField(
        value = identity.customerName,
        onValueChange = actions.onCustomerName,
        label = stringResource(Res.string.cashier_customer),
        suggestions = suggestions,
        onPick = { picked -> identity.customerSuggestions.firstOrNull { it.id == picked.key }?.let(actions.onPickCustomer) },
        linked = identity.customerLinked,
        linkedDescription = stringResource(Res.string.cashier_customer_linked),
        // Enter pindah ke isian berikutnya tanpa membuang isian atau menutup panel.
        keyboardOptions = KeyboardOptions(imeAction = ImeAction.Next),
        keyboardActions = KeyboardActions(onNext = { focus.moveFocus(FocusDirection.Down) }),
    )
    identity.suggestionFailure?.let { InlineMessage(text = failureText(it)) }
}

@Composable
private fun NoteField(identity: OrderIdentity, actions: OrderIdentityActions, notFilled: String) {
    Column(verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.xs)) {
        DropdownField(
            label = stringResource(Res.string.cashier_order_note),
            options = listOf(DropdownOption(null, notFilled)) + identity.notes.map { DropdownOption(it.id, it.name) },
            selectedKey = identity.noteId,
            onSelect = actions.onNote,
            searchLabel = stringResource(Res.string.cashier_order_note_search),
            emptyText = stringResource(Res.string.cashier_order_note_empty),
            addLabel = { typed -> stringResource(Res.string.cashier_order_note_add, typed) },
            onAdd = actions.onAddNote,
            searchMaxLength = OrderNoteMaxLength,
        )
        identity.noteFailure?.let { InlineMessage(text = failureText(it)) }
    }
}
