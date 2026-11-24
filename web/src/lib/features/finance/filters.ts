import { access } from '$lib/auth/access.svelte';
import type { Filters } from '$lib/components/filter/filters.svelte';
import { createReportFilters } from '../report/filters';
import { termText } from '$lib/text/terms';
import { financeText } from '$lib/text/finance';

export function createFinanceFilters(): Filters {
	return createReportFilters([
		{
			kind: 'select',
			key: 'status_qc',
			label: financeText.qcStatus,
			options: [
				{ value: 'balanced', label: financeText.qcMatch },
				{ value: 'mismatch', label: termText.difference },
				{ value: 'pending', label: financeText.qcNotFilled }
			]
		},
		{
			kind: 'select',
			key: 'kelompok_bayar',
			label: financeText.paymentGroup,
			options: [
				{ value: 'cash', label: financeText.cash },
				{ value: 'non_cash', label: termText.nonCash }
			]
		},
		{ kind: 'select', key: 'metode', label: financeText.paymentMethod, options: [] },
		{ kind: 'select', key: 'batal', label: financeText.voidedTransactions, options: [{ value: 'ya', label: financeText.include }] },
		...(access.allows('view_deposits')
			? [
					{
						kind: 'select' as const,
						key: 'setoran',
						label: financeText.deposit,
						options: [
							{ value: 'dipegang', label: financeText.stillHeld },
							{ value: 'lunas', label: financeText.alreadyDeposited }
						]
					}
				]
			: [])
	]);
}
