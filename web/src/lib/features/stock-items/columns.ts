import type { StockCard, StockItem } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE, formatNumber, formatRupiah } from '$lib/format/currency';
import { formatDateTime } from '$lib/format/datetime';
import { CARD_KINDS, STOCK_STATUS } from './labels';
import { termText } from '$lib/text/terms';
import { stockItemText } from '$lib/text/stock-items';

export const stockColumns: Column<StockItem>[] = [
	{ key: 'barang', label: stockItemText.item, align: 'left', value: (row) => row.menu_item_name, sort: 'name' },
	{ key: 'saldo', label: stockItemText.balance, value: (row) => `${formatNumber(row.balance)} ${row.unit ?? ''}`.trim(), sort: 'balance' },
	{ key: 'modal', label: stockItemText.cost, value: (row) => (row.cost === null ? EMPTY_VALUE : formatRupiah(row.cost)), sort: 'cost' },
	{ key: 'nilai', label: stockItemText.inventoryValue, value: (row) => (row.inventory_value === null ? EMPTY_VALUE : formatRupiah(row.inventory_value)), sort: 'value' },
	{ key: 'status', label: termText.status, align: 'left', value: (row) => STOCK_STATUS[row.status]?.label ?? row.status, sort: 'status' }
];

export const cardColumns: Column<StockCard>[] = [
	{ key: 'waktu', label: termText.time, align: 'left', value: (row) => formatDateTime(row.created_at), sort: 'created_at' },
	{ key: 'jenis', label: termText.kind, align: 'left', value: (row) => CARD_KINDS[row.kind] ?? row.kind, sort: 'kind' },
	{ key: 'jumlah', label: termText.quantity, value: (row) => `${Number(row.qty) > 0 ? '+' : ''}${formatNumber(row.qty)}`, sort: 'qty' },
	{ key: 'harga', label: stockItemText.cost, value: (row) => (row.unit_price === null ? EMPTY_VALUE : formatRupiah(row.unit_price)), sort: 'unit_price' },
	{ key: 'pencatat', label: termText.recordedBy, align: 'left', value: (row) => row.user_name ?? EMPTY_VALUE, sort: 'user' }
];
