import { get } from 'svelte/store';
import { scopeText } from '$lib/components/form/branch-prices.svelte';
import { branches } from '$lib/stores/branch';
import { controlText } from '$lib/text/controls';
import type { Announcement, Promo } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { formatDate } from '$lib/date/range';
import { formatNumber, formatRupiah } from '$lib/format/currency';
import { KIND_LABELS } from './labels';
import { termText } from '$lib/text/terms';
import { promotionText } from '$lib/text/promotions';
import { format } from '$lib/text/format';

const period = (row: { starts_on: string; ends_on: string }) => `${formatDate(row.starts_on)} – ${formatDate(row.ends_on)}`;
const cut = (row: Promo) => (row.discount_type === 'persen' ? `${formatNumber(row.value)}%` : formatRupiah(row.value));
const target = (row: Promo) => {
	if (row.kind === 'produk') return format(controlText.menusCount, { count: formatNumber(row.product_ids.length, 0) });
	if (row.kind === 'total') return format(promotionText.minimumShort, { amount: formatRupiah(row.minimum_spend ?? 0) });
	return KIND_LABELS[row.kind] ?? row.kind;
};

/** A percent and a rupiah cut are not on one scale, so the cut column is not sortable. */
export const promoColumns: Column<Promo>[] = [
	{ key: 'promo', label: termText.promo, align: 'left', value: (row) => row.name, sort: 'name' },
	{ key: 'jenis', label: promotionText.appliesTo, align: 'left', value: target, sort: 'kind' },
	{ key: 'cabang', label: termText.branch, align: 'left', value: (row) => scopeText(row.outlet_id, get(branches)) },
	{ key: 'aktivasi', label: promotionText.activation, align: 'left', value: (row) => (row.activation === 'manual' ? promotionText.chosenByCashier : promotionText.automatic), sort: 'activation' },
	{ key: 'periode', label: termText.period, align: 'left', value: period, sort: 'period' },
	{ key: 'potongan', label: termText.discount, value: cut, class: () => 'font-semibold' }
];

export const announcementColumns: Column<Announcement>[] = [
	{ key: 'promosi', label: promotionText.announcement, align: 'left', value: (row) => row.title, sort: 'title' },
	{ key: 'cabang', label: termText.branch, align: 'left', value: (row) => scopeText(row.outlet_id, get(branches)) },
	{ key: 'periode', label: termText.period, align: 'left', value: period, sort: 'period' }
];
