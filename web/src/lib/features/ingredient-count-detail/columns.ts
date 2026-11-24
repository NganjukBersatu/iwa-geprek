import type { IngredientCountChange, StockRow } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE, formatNumber } from '$lib/format/currency';
import { formatDateTime } from '$lib/format/datetime';
import { termText } from '$lib/text/terms';
import { ingredientCountText } from '$lib/text/ingredient-counts';
import { ingredientCountDetailText } from '$lib/text/ingredient-count-detail';
import { movementColumns } from '../ingredient-counts/columns';

export type LineStatus = 'uncounted' | 'match' | 'difference' | 'check';

export const STATUS_LABELS: Record<LineStatus, string> = {
	uncounted: ingredientCountDetailText.notCounted,
	match: ingredientCountDetailText.match,
	difference: termText.difference,
	check: ingredientCountText.systemMinus
};

export const STATUS_TONES = { uncounted: 'neutral', match: 'success', difference: 'warning', check: 'danger' } as const;

/** Satu bahan penutupan: tidak dihitung, cocok, berselisih, atau stok sistemnya minus sehingga selisihnya tidak bisa dinilai. */
export function lineStatus(row: StockRow): LineStatus {
	if (row.counted === null) return 'uncounted';
	if (row.replacement_status === 'check') return 'check';
	return Number(row.difference ?? 0) === 0 ? 'match' : 'difference';
}

export const signed = (value: string | null): string => {
	if (value === null) return EMPTY_VALUE;
	const number = Number(value);
	return `${number > 0 ? '+' : ''}${formatNumber(number)}`;
};

/** Satu tampilan untuk setiap periode yang sudah ditutup: pergerakan stok, lalu jumlah fisik, selisih, dan status. */
export const detailColumns: Column<StockRow>[] = [
	...movementColumns.map(({ sort: _sort, ...column }) => column),
	{ key: 'real', label: termText.physicalCount, value: (row) => (row.counted === null ? EMPTY_VALUE : formatNumber(Number(row.counted))) },
	{ key: 'selisih', label: termText.difference, value: (row) => signed(row.difference) },
	{ key: 'status', label: termText.status, align: 'left', value: (row) => STATUS_LABELS[lineStatus(row)] }
];

const shown = (value: string | null): string => (value === null ? 'belum ada' : formatNumber(Number(value)));


export const changeColumns: Column<IngredientCountChange>[] = [
	{ key: 'waktu', label: termText.time, align: 'left', value: (row) => formatDateTime(row.created_at), sort: 'time' },
	{ key: 'bahan', label: termText.ingredient, align: 'left', value: (row) => row.ingredient_name, sort: 'ingredient' },
	{ key: 'perubahan', label: ingredientCountDetailText.changes, align: 'left', value: (row) => (row.action === 'remove' ? `${shown(row.old_counted)} → dihapus dari periode` : `${shown(row.old_counted)} → ${shown(row.new_counted)}`) },
	{ key: 'oleh', label: termText.by, align: 'left', value: (row) => row.user_name ?? EMPTY_VALUE, sort: 'user' }
];
