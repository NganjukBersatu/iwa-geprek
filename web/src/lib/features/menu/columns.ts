import type { MenuItem } from '$lib/api/types';
import { sellersText } from '$lib/components/form/branch-prices.svelte';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE, formatRupiah } from '$lib/format/currency';
import { termText } from '$lib/text/terms';
import { menuText } from '$lib/text/menu';

export const menuColumns = (outlets: { id: string; name: string }[]): Column<MenuItem>[] => {
	return [
		{ key: 'menu', label: termText.menu, align: 'left', value: (row) => row.name, sort: 'name' },
		{ key: 'kategori', label: termText.category, align: 'left', value: (row) => row.category_name ?? EMPTY_VALUE, sort: 'category' },
		{ key: 'cabang', label: menuText.soldIn, align: 'left', value: (row) => sellersText(row, outlets) },
		{ key: 'harga', label: termText.basePrice, value: (row) => formatRupiah(row.price), class: () => 'font-semibold', sort: 'price' }
	];
};
