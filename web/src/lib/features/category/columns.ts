import type { CategorySales, MenuSales, UnsoldMenu } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE, formatNumber, formatPercentPlain, formatRupiah, formatRupiahOrDash } from '$lib/format/currency';
import { formatDay } from '$lib/format/datetime';
import { termText } from '$lib/text/terms';
import { categoryReportText } from '$lib/text/category-report';

/** Perubahan omzet terhadap periode sebelumnya; "Baru" bila periode sebelumnya belum ada penjualan di kategori itu. */
export function changeText(row: CategorySales): string {
	if (row.revenue_change_percent !== null) {
		return `${Number(row.revenue_change_percent) > 0 ? '+' : ''}${formatPercentPlain(row.revenue_change_percent)}`;
	}
	return Number(row.previous_revenue) === 0 && Number(row.revenue) > 0 ? categoryReportText.newCategory : EMPTY_VALUE;
}

export const categoryColumns: Column<CategorySales>[] = [
	{ key: 'kategori', label: termText.category, value: (row) => row.category, sort: 'category' },
	{ key: 'qty', label: categoryReportText.quantity, value: (row) => formatNumber(row.qty, 0), sort: 'qty' },
	{ key: 'omzet', label: termText.revenue, value: (row) => formatRupiah(row.revenue), class: () => 'font-semibold', sort: 'revenue' },
	{ key: 'laba', label: termText.profit, value: (row) => formatRupiahOrDash(row.profit), sort: 'profit' },
	{ key: 'perubahan', label: categoryReportText.change, value: changeText, sort: 'change' },
	{ key: 'persen', label: '%', value: (row) => formatPercentPlain(row.revenue_percent), class: () => 'text-slate-500' }
];

export const menuColumns: Column<MenuSales>[] = [
	{ key: 'menu', label: termText.menu, value: (row) => row.name, sort: 'name' },
	{ key: 'qty', label: categoryReportText.quantity, value: (row) => formatNumber(row.qty, 0), sort: 'qty' },
	{ key: 'omzet', label: termText.revenue, value: (row) => formatRupiah(row.revenue), class: () => 'font-semibold', sort: 'revenue' },
	{ key: 'laba', label: termText.profit, value: (row) => formatRupiahOrDash(row.profit), sort: 'profit' }
];

export const unsoldColumns: Column<UnsoldMenu>[] = [
	{ key: 'name', label: termText.menu, value: (row) => row.name, sort: 'name' },
	{ key: 'category', label: termText.category, align: 'left', value: (row) => row.category ?? termText.noCategory, sort: 'category' },
	{ key: 'price', label: termText.price, value: (row) => formatRupiah(row.price), sort: 'price' },
	{ key: 'created', label: categoryReportText.addedToCatalog, value: (row) => formatDay(row.created_at), sort: 'created' },
	{ key: 'last', label: categoryReportText.lastSold, value: (row) => (row.last_sold_at ? formatDay(row.last_sold_at) : categoryReportText.neverSold), sort: 'last_sold' }
];
