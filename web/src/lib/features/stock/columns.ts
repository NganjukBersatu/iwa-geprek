import { QUIET_VALUE } from '$lib/components/table/quiet-value';
import type { StockRow } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { formatNumberOrDash, formatPercentOrDash, formatRupiahOrDash } from '$lib/format/currency';
import { REPLACEMENT } from './labels';
import { termText } from '$lib/text/terms';
import { stockReportText } from '$lib/text/stock-report';

const negative = (value: string | null) => value !== null && Number(value) < 0;

export const stockColumns: Column<StockRow>[] = [
	{ key: 'nama', label: termText.ingredient, align: 'left', value: (row) => row.name, sort: 'name' },
	{ key: 'satuan', label: termText.unit, align: 'left', value: (row) => row.unit, class: () => 'text-slate-500', sort: 'unit' },
	{ key: 'nilai', label: stockReportText.value, value: (row) => formatRupiahOrDash(row.unit_price), sort: 'unit_price' },
	{ key: 'stok_awal', label: stockReportText.openingStock, value: (row) => formatNumberOrDash(row.opening_stock), sort: 'opening' },
	{ key: 'belanja', label: termText.purchase, value: (row) => formatNumberOrDash(row.purchased), sort: 'purchased' },
	{ key: 'pengeluaran', label: termText.usedStock, value: (row) => formatNumberOrDash(row.used), sort: 'used' },
	{ key: 'rusak', label: termText.damaged, value: (row) => formatNumberOrDash(row.wasted), sort: 'wasted' },
	{ key: 'rnd', label: 'RnD', value: (row) => formatNumberOrDash(row.rnd), sort: 'rnd' },
	{ key: 'penyesuaian', label: stockReportText.adjustment, value: (row) => formatNumberOrDash(row.adjustment), class: (row) => (Number(row.adjustment) === 0 ? QUIET_VALUE : ''), sort: 'adjustment' },
	{ key: 'stok_akhir', label: stockReportText.closingStock, value: (row) => formatNumberOrDash(row.closing_stock), class: (row) => (negative(row.closing_stock) ? 'font-semibold text-warning-700' : 'font-semibold'), sort: 'closing' },
	{ key: 'real', label: termText.physicalCount, value: (row) => formatNumberOrDash(row.counted), sort: 'counted' },
	{ key: 'diferensiasi', label: stockReportText.differentiation, value: (row) => formatNumberOrDash(row.difference), class: (row) => (negative(row.difference) ? 'text-danger-700' : ''), sort: 'difference' },
	{ key: 'presentase_minus', label: stockReportText.minusPercent, value: (row) => formatPercentOrDash(row.shrink_percent, 2), sort: 'shrink_percent' },
	{ key: 'nilai_stok_sistem', label: stockReportText.systemStockValue, value: (row) => formatRupiahOrDash(row.book_value), sort: 'book_value' },
	{ key: 'nilai_stok_real', label: stockReportText.physicalStockValue, value: (row) => formatRupiahOrDash(row.counted_value), sort: 'counted_value' },
	{ key: 'nilai_diferensial', label: stockReportText.differentialValue, value: (row) => formatRupiahOrDash(row.difference_value), class: () => 'font-medium', sort: 'difference_value' },
	{ key: 'toleransi_minus', label: stockReportText.minusTolerance, value: (row) => formatPercentOrDash(row.shrink_tolerance, 2), class: () => 'text-slate-500', sort: 'tolerance' },
	{ key: 'status', label: stockReportText.reimbursementStatus, align: 'left', value: (row) => REPLACEMENT[row.replacement_status].label, sort: 'status' }
];
