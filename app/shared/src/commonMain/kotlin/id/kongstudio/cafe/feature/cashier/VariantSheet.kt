package id.kongstudio.cafe.feature.cashier

import androidx.compose.foundation.layout.Arrangement
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.apptext.AppText
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.cashier_add_to_order
import id.kongstudio.cafe.resources.cashier_extras
import id.kongstudio.cafe.resources.cashier_note
import id.kongstudio.cafe.resources.cashier_variant_required
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.choicegroup.ChoiceGroup
import id.kongstudio.cafe.ui.component.quantitystepper.QuantityStepper
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

/** Pilihan varian, ekstra, dan catatan untuk satu menu sebelum masuk pesanan. */
@Composable
internal fun VariantSheet(
    item: CashierItem,
    onDismiss: () -> Unit,
    onConfirm: (variantIds: List<String>, extras: Map<String, Int>, note: String?) -> Unit,
) {
    val spacing = AppTheme.spacing
    val chosen = remember(item.id) { mutableStateMapOf<String, String>() }
    val extras = remember(item.id) { mutableStateMapOf<String, Int>() }
    var note by remember(item.id) { mutableStateOf("") }
    val requiredLabel = stringResource(Res.string.cashier_variant_required)
    val complete = item.variants.all { !it.required || chosen.containsKey(it.id) }

    AppBottomSheet(title = item.name, onDismiss = onDismiss) {
        Column(verticalArrangement = Arrangement.spacedBy(spacing.md)) {
            item.variants.forEach { group ->
                ChoiceGroup(
                    label = if (group.required) "${group.name} - $requiredLabel" else group.name,
                    options = group.options.map { it.name },
                    selectedIndex = group.options.indexOfFirst { it.id == chosen[group.id] }.takeIf { it >= 0 },
                    onSelect = { chosen[group.id] = group.options[it].id },
                )
            }

            if (item.extras.isNotEmpty()) {
                AppText(
                    text = stringResource(Res.string.cashier_extras),
                    role = TextRole.Label,
                    color = AppTheme.colors.content,
                )
                item.extras.forEach { extra ->
                    val count = extras[extra.id] ?: 0
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween,
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            AppText(
                                text = extra.name,
                                role = TextRole.Body,
                                color = AppTheme.colors.content,
                            )
                            AppText(
                                text = formatRupiah(extra.price),
                                role = TextRole.Label,
                                color = AppTheme.colors.contentMuted,
                            )
                        }
                        QuantityStepper(
                            quantity = count,
                            onDecrease = { if (count > 0) extras[extra.id] = count - 1 },
                            onIncrease = { extras[extra.id] = count + 1 },
                            removable = false,
                        )
                    }
                }
            }

            AppTextField(
                value = note,
                onValueChange = { if (it.length <= LineNoteMaxLength) note = it },
                label = stringResource(Res.string.cashier_note),
            )
            PrimaryButton(
                text = stringResource(Res.string.cashier_add_to_order),
                onClick = {
                    onConfirm(chosen.values.toList(), extras.filterValues { it > 0 }, note.trim().ifEmpty { null })
                },
                enabled = complete,
                modifier = Modifier.padding(bottom = spacing.sm),
            )
        }
    }
}
