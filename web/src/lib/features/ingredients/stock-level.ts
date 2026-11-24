import type { Ingredient } from '$lib/api/types';
import type { Tone } from '$lib/components/card/tone';
import { ingredientText } from '$lib/text/ingredients';

export type StockBadge = { tone: Tone; label: string };
type Level = NonNullable<Ingredient['stock_level']>;

/** Satu penanda per tingkat stok, supaya daftar dan detail menyebut kekurangan yang sama dengan nama yang sama. */
export function stockBadge(level: Level, compact = false): StockBadge {
	switch (level) {
		case 'negative':
			return { tone: 'danger', label: compact ? ingredientText.negative : ingredientText.negativeStock };
		case 'out':
			return { tone: 'warning', label: compact ? ingredientText.out : ingredientText.outStock };
		case 'low':
			return { tone: 'warning', label: compact ? ingredientText.low : ingredientText.lowStock };
	}
}
