import { controlText } from '$lib/text/controls';
import type { Extra, VariantGroup } from '$lib/api/types';
import { get } from 'svelte/store';
import { scopeText, sellersText, type BranchOption } from '$lib/components/form/branch-prices.svelte';
import { branches } from '$lib/stores/branch';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE, formatNumber, formatRupiah } from '$lib/format/currency';
import { termText } from '$lib/text/terms';
import { optionText } from '$lib/text/options';
import { format } from '$lib/text/format';

export const groupColumns: Column<VariantGroup>[] = [
	{ key: 'kelompok', label: optionText.group, align: 'left', value: (row) => row.name, sort: 'name' },
	{ key: 'cabang', label: termText.branch, align: 'left', value: (row) => scopeText(row.outlet_id, get(branches)) },
	{ key: 'pilihan', label: optionText.choices, align: 'left', value: (row) => row.choices.map((choice) => choice.name).join(', '), sort: 'choices' },
	{ key: 'menu', label: termText.menu, value: (row) => format(controlText.menusCount, { count: formatNumber(row.menu_ids.length, 0) }), sort: 'menus' }
];

/** Berlaku di sorts by how many branches an extra reaches, every branch counting as the most. */
export function extraColumns(outlets: BranchOption[]): Column<Extra>[] {
	return [
		{ key: 'ekstra', label: termText.extra, align: 'left', value: (row) => row.name, sort: 'name' },
		{ key: 'kategori', label: termText.category, align: 'left', value: (row) => row.category_name ?? EMPTY_VALUE, sort: 'category' },
		{ key: 'cabang', label: optionText.availableIn, align: 'left', value: (row) => sellersText(row, outlets), sort: 'branches' },
		{ key: 'menu', label: termText.menu, value: (row) => format(controlText.menusCount, { count: formatNumber(row.menu_ids.length, 0) }), sort: 'menus' },
		{ key: 'harga', label: termText.basePrice, value: (row) => formatRupiah(row.price), class: () => 'font-semibold', sort: 'price' }
	];
}
