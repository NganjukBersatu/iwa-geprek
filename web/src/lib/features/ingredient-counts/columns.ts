import type { StockRow } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE, formatNumber, formatNumberOrDash } from '$lib/format/currency';
import { formatDate } from '$lib/date/range';
import { formatDateTime } from '$lib/format/datetime';
import { termText } from '$lib/text/terms';
import { ingredientCountText } from '$lib/text/ingredient-counts';
import { format } from '$lib/text/format';

/** Pergerakan stok satu periode; dipakai lembar opname dan halaman periode yang sudah ditutup supaya tampilannya sama. */
export const movementColumns: Column<StockRow>[] = [
	{ key: 'bahan', label: termText.ingredient, align: 'left', value: (row) => row.name, sort: 'name' },
	{ key: 'satuan', label: ingredientCountText.unitShort, align: 'left', value: (row) => row.unit, sort: 'unit' },
	{ key: 'awal', label: ingredientCountText.openingStock, value: (row) => formatNumberOrDash(row.opening_stock), sort: 'opening' },
	{ key: 'belanja', label: termText.purchase, value: (row) => formatNumberOrDash(row.purchased), sort: 'purchased' },
	{ key: 'pengeluaran', label: termText.usedStock, value: (row) => formatNumberOrDash(row.used), sort: 'used' },
	{ key: 'rusak', label: termText.damaged, value: (row) => formatNumberOrDash(row.wasted), sort: 'wasted' },
	{ key: 'rnd', label: 'RnD', value: (row) => formatNumberOrDash(row.rnd), sort: 'rnd' },
	{ key: 'penyesuaian', label: ingredientCountText.adjustment, value: (row) => formatNumberOrDash(row.adjustment), sort: 'adjustment' },
	{ key: 'akhir', label: ingredientCountText.closingStock, value: (row) => formatNumberOrDash(row.closing_stock), class: () => 'font-semibold', sort: 'closing' }
];

/** The count and difference cells are typed on screen, so they are not sorted. */
export const sheetColumns: Column<StockRow>[] = [
	...movementColumns,
	{ key: 'real', label: termText.physicalCount, value: () => '' },
	{ key: 'selisih', label: termText.difference, value: () => '' }
];

export const SOURCE_LABELS: Record<string, string> = { web: ingredientCountText.sourceWeb, tablet: ingredientCountText.sourceTablet };

/** Keadaan satu baris riwayat: bagian yang menjadi stok awal, periode yang harus ditutup, periode berjalan, atau sudah ditutup. */
export type HistoryState = 'opening' | 'absorbed' | 'to_close' | 'running' | 'closed';

export const HISTORY_TONES: Record<HistoryState, 'neutral' | 'warning' | 'success' | 'info'> = {
	opening: 'info',
	absorbed: 'neutral',
	to_close: 'warning',
	running: 'success',
	closed: 'neutral'
};

/** One line of the history: a period already closed, or a period a branch has not closed yet. */
export type CountHistoryRow = {
	key: string;
	/** Empty while the period is still running. */
	id: string | null;
	/** Bagian yang ikut tertutup oleh opname `id`: hari pertamanya, untuk membuka halaman rincian yang sama. */
	part_start: string | null;
	running: boolean;
	state: HistoryState;
	/** Nama periode cabang tempat baris ini berada, dinamai menurut bulan tanggal akhirnya. */
	name: string;
	/** A tablet has asked to close this running period and the request is still waiting. */
	requested: boolean;
	outlet_id: string;
	outlet_name: string;
	start: string;
	end: string | null;
	note: string | null;
	user_name: string | null;
	source: string | null;
	ingredient_count: number | null;
	created_at: string | null;
	days: number | null;
};

/** Teks periode satu baris riwayat, sama di kolom dan di baris pertama. */
export const historyPeriod = (row: CountHistoryRow): string =>
	format(ingredientCountText.periodRange, { name: row.name, from: formatDate(row.start), to: row.end ? formatDate(row.end) : ingredientCountText.periodNow });

export const historyColumns: Column<CountHistoryRow>[] = [
	{ key: 'periode', label: termText.period, align: 'left', value: historyPeriod, sort: 'period' },
	{ key: 'status', label: termText.status, align: 'left', value: (row) => (row.requested ? ingredientCountText.requestedStatus : ingredientCountText.historyStates[row.state]) },
	{ key: 'petugas', label: ingredientCountText.user, align: 'left', value: (row) => row.user_name ?? EMPTY_VALUE, sort: 'user' },
	{ key: 'sumber', label: ingredientCountText.source, align: 'left', value: (row) => (row.source ? (SOURCE_LABELS[row.source] ?? row.source) : EMPTY_VALUE) },
	{ key: 'bahan', label: ingredientCountText.countedIngredients, value: (row) => (row.ingredient_count === null ? EMPTY_VALUE : formatNumber(row.ingredient_count, 0)), sort: 'ingredients' },
	{ key: 'ditutup', label: termText.closed, align: 'left', value: (row) => (row.created_at ? formatDateTime(row.created_at) : EMPTY_VALUE), sort: 'closed_at' }
];
