import { controlText } from '$lib/text/controls';
import type { PaymentMethod } from '$lib/api/types';
import type { Tone } from '$lib/components/card/tone';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE, formatNumber, formatPercentPlain } from '$lib/format/currency';
import { termText } from '$lib/text/terms';
import { paymentMethodText } from '$lib/text/payment-methods';
import { format } from '$lib/text/format';

export type MethodStatus = { label: string; tone: Tone; icon: string };

/** Keadaan metode di kasir: nonaktif, belum lengkap sehingga belum bisa dipilih, atau siap. */
export function methodStatus(row: PaymentMethod): MethodStatus {
	if (!row.is_active) return { label: termText.inactive, tone: 'neutral', icon: 'circle-off' };
	if (row.missing.length > 0) return { label: paymentMethodText.statusIncomplete, tone: 'warning', icon: 'alert-triangle' };
	return { label: paymentMethodText.statusReady, tone: 'success', icon: 'circle-check' };
}

/** Isian yang belum ada, untuk keterangan badge Belum lengkap; kosong bila sudah lengkap. */
export const missingText = (row: PaymentMethod): string | undefined => (row.missing.length > 0 ? format(paymentMethodText.notFilledList, { fields: row.missing.join(' dan ') }) : undefined);

export const paymentMethodColumns: Column<PaymentMethod>[] = [
	{ key: 'metode', label: termText.method, align: 'left', value: (row) => row.label, sort: 'label' },
	{ key: 'status', label: termText.status, align: 'left', value: (row) => (row.is_active && row.missing.length > 0 ? (missingText(row) ?? '') : methodStatus(row).label), sort: 'missing' },
	{ key: 'kembalian', label: paymentMethodText.change, align: 'left', value: (row) => (row.needs_change ? termText.yes : termText.no), sort: 'needs_change' },
	{ key: 'biaya', label: paymentMethodText.fee, value: (row) => (Number(row.fee_percent) > 0 ? formatPercentPlain(row.fee_percent) : EMPTY_VALUE), sort: 'fee' },
	{ key: 'dipakai', label: paymentMethodText.inUse, value: (row) => (row.used_by_orders > 0 ? format(controlText.ordersCount, { count: formatNumber(row.used_by_orders, 0) }) : EMPTY_VALUE), sort: 'used' }
];
