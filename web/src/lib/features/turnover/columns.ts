import { controlText } from '$lib/text/controls';
import { QUIET_VALUE } from '$lib/components/table/quiet-value';
import type { TurnoverRow } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE, formatNumber, formatRupiah } from '$lib/format/currency';
import { statusLabels } from './labels';
import { termText } from '$lib/text/terms';
import { turnoverText } from '$lib/text/turnover';
import { format } from '$lib/text/format';

const qty = (value: string) => formatNumber(value, 3);
const left = (row: TurnoverRow) => (row.status === 'out' ? 'habis' : row.days_of_stock === null ? EMPTY_VALUE : row.days_of_stock === 0 ? 'hari ini' : format(controlText.daysCount, { count: row.days_of_stock }));
const moved = (row: TurnoverRow) => (row.days_since_movement === null ? 'belum pernah' : row.days_since_movement === 0 ? 'hari ini' : format(turnoverText.daysAgo, { count: row.days_since_movement }));
const advice = (row: TurnoverRow) => (Number(row.suggested_purchase) > 0 ? `${qty(row.suggested_purchase)} ${row.unit}` : EMPTY_VALUE);

export const turnoverColumns: Column<TurnoverRow>[] = [
	{ key: 'nama', label: termText.ingredient, align: 'left', value: (row) => row.name, sort: 'name' },
	{ key: 'satuan', label: termText.unit, align: 'left', value: (row) => row.unit, class: () => 'text-slate-500', sort: 'unit' },
	{ key: 'stok', label: termText.stock, value: (row) => qty(row.closing_stock), class: (row) => (Number(row.closing_stock) <= 0 ? 'font-semibold text-danger-700' : 'font-semibold'), sort: 'stock' },
	{ key: 'terjual', label: turnoverText.sold, value: (row) => qty(row.sold), sort: 'sold' },
	{ key: 'susut', label: turnoverText.shrinkage, value: (row) => qty(row.shrinkage), class: (row) => (Number(row.shrinkage) > 0 ? 'text-warning-700' : QUIET_VALUE), sort: 'shrinkage' },
	{ key: 'harian', label: 'Pakai/Hari', value: (row) => qty(row.daily_usage), sort: 'daily_usage' },
	{
		key: 'sisa',
		label: termText.remaining,
		value: left,
		class: (row) => (row.status === 'out' ? 'font-semibold text-danger-700' : row.status === 'urgent' ? 'font-semibold text-warning-700' : 'font-semibold'),
		sort: 'days_left'
	},
	{
		key: 'perputaran',
		label: turnoverText.turnover,
		value: (row) => (row.turnover === null ? EMPTY_VALUE : `${formatNumber(row.turnover, 2)}×`),
		class: () => 'text-slate-500',
		sort: 'turnover'
	},
	{ key: 'gerak', label: turnoverText.lastMovement, value: moved, class: (row) => (row.status === 'dormant' ? 'font-medium text-category-700' : 'text-slate-500'), sort: 'idle_days' },
	{ key: 'nilai', label: turnoverText.value, value: (row) => formatRupiah(row.stock_value), sort: 'value' },
	{ key: 'saran', label: turnoverText.purchaseAdvice, value: advice, class: (row) => (Number(row.suggested_purchase) > 0 ? 'font-bold text-brand' : QUIET_VALUE), sort: 'suggested' },
	{ key: 'status', label: termText.status, align: 'left', value: (row) => statusLabels[row.status], sort: 'status' }
];
