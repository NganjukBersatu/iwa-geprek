import { controlText } from '$lib/text/controls';
import type { PaymentMethod } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE, formatNumber, formatPercentPlain } from '$lib/format/currency';
import { termText } from '$lib/text/terms';
import { paymentMethodText } from '$lib/text/payment-methods';
import { format } from '$lib/text/format';

export const paymentMethodColumns: Column<PaymentMethod>[] = [
	{ key: 'metode', label: termText.method, align: 'left', value: (row) => row.label, sort: 'label' },
	{ key: 'kelengkapan', label: paymentMethodText.completeness, align: 'left', value: (row) => (row.missing.length === 0 ? paymentMethodText.complete : format(paymentMethodText.notFilledList, { fields: row.missing.join(' dan ') })), sort: 'missing' },
	{ key: 'kembalian', label: paymentMethodText.change, align: 'left', value: (row) => (row.needs_change ? termText.yes : termText.no), sort: 'needs_change' },
	{ key: 'biaya', label: paymentMethodText.fee, value: (row) => (Number(row.fee_percent) > 0 ? formatPercentPlain(row.fee_percent) : EMPTY_VALUE), sort: 'fee' },
	{ key: 'dipakai', label: paymentMethodText.inUse, value: (row) => (row.used_by_orders > 0 ? format(controlText.ordersCount, { count: formatNumber(row.used_by_orders, 0) }) : EMPTY_VALUE), sort: 'used' }
];
