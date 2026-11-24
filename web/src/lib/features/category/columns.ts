import type { CategorySales, UnsoldMenu } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { formatDate } from '$lib/date/range';
import { formatNumber, formatPercentPlain, formatRupiah } from '$lib/format/currency';
import { termText } from '$lib/text/terms';
import { categoryReportText } from '$lib/text/category-report';

export const categoryColumns: Column<CategorySales>[] = [
	{ key: 'kategori', label: termText.category, value: (row) => row.category, sort: 'category' },
	{ key: 'qty', label: categoryReportText.quantity, value: (row) => formatNumber(row.qty, 0), sort: 'qty' },
	{ key: 'omzet', label: termText.revenue, value: (row) => formatRupiah(row.revenue), class: () => 'font-semibold', sort: 'revenue' },
	{ key: 'persen', label: '%', value: (row) => formatPercentPlain(row.revenue_percent), class: () => 'text-slate-500' }
];

export const unsoldColumns: Column<UnsoldMenu>[] = [
	{ key: 'name', label: termText.menu, value: (row) => row.name, sort: 'name' },
	{ key: 'category', label: termText.category, align: 'left', value: (row) => row.category ?? termText.noCategory, sort: 'category' },
	{ key: 'price', label: termText.price, value: (row) => formatRupiah(row.price), sort: 'price' },
	{ key: 'last', label: categoryReportText.lastSold, value: (row) => (row.last_sold_at ? formatDate(row.last_sold_at.slice(0, 10)) : 'belum pernah'), sort: 'last_sold' }
];
