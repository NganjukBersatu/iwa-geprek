package id.kongstudio.cafe.feature.ingredientstock

import id.kongstudio.cafe.core.format.StockQuantity
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.ingredient_status_low
import id.kongstudio.cafe.resources.ingredient_status_negative
import id.kongstudio.cafe.resources.ingredient_status_safe
import id.kongstudio.cafe.resources.movement_kind_adjustment
import id.kongstudio.cafe.resources.movement_kind_in
import id.kongstudio.cafe.resources.movement_kind_sale
import id.kongstudio.cafe.resources.movement_kind_trial
import id.kongstudio.cafe.resources.movement_kind_use
import id.kongstudio.cafe.resources.movement_kind_waste
import id.kongstudio.cafe.resources.stock_opening
import org.jetbrains.compose.resources.StringResource

internal fun movementKindLabel(movement: StockMovement): StringResource? = when {
    movement.fromOpening -> Res.string.stock_opening
    else -> when (movement.kind) {
        CardKind.In -> Res.string.movement_kind_in
        // Kartu keluar tanpa penjualan adalah pemakaian manual bahan tidak langsung.
        CardKind.Out -> if (movement.fromSale) Res.string.movement_kind_sale else Res.string.movement_kind_use
        CardKind.Waste -> Res.string.movement_kind_waste
        CardKind.Trial -> Res.string.movement_kind_trial
        CardKind.Adjustment -> Res.string.movement_kind_adjustment
        CardKind.Other -> null
    }
}

internal fun stockStatusLabel(ingredient: StockIngredient): StringResource = when {
    StockQuantity.isNegative(ingredient.stock) -> Res.string.ingredient_status_negative
    ingredient.low -> Res.string.ingredient_status_low
    else -> Res.string.ingredient_status_safe
}
