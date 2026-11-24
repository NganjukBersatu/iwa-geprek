<script lang="ts">
	import { goto } from '$app/navigation';
	import { mutationPath } from '$lib/nav/pages';
	import type { MutationPage } from '$lib/api/types';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import SummaryCard from '$lib/components/card/SummaryCard.svelte';
	import Pager from '$lib/components/pager/Pager.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { EMPTY_VALUE, formatNumber, formatRupiah, formatSigned } from '$lib/format/currency';
	import type { MutationsState } from '../mutations.svelte';
	import { mutationColumns } from '../columns';
	import { termText } from '$lib/text/terms';
	import { mutationText } from '$lib/text/mutations';
	import { format } from '$lib/text/format';

	let { data, mutations }: { data: MutationPage; mutations: MutationsState } = $props();

	const summary = $derived(data.summary);
	const differences = $derived([summary.float_difference, summary.shopping_difference, summary.revenue_difference].map(Number));

	const columns = mutationColumns;
</script>

<div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-4">
	<SummaryCard label={mutationText.session} caption={format(mutationText.alreadyClosed, { count: formatNumber(summary.closed, 0) })} value={formatNumber(summary.sessions, 0)} icon="clock" accent="primary" />
	<SummaryCard label={mutationText.cashRevenue} caption={format(mutationText.nonCashToAccount, { amount: formatRupiah(summary.non_cash_revenue) })} value={formatRupiah(summary.cash_revenue)} icon="cash" accent="green" />
	<SummaryCard
		label={termText.purchase}
		caption={format(mutationText.expensesBreakdown, { cash: formatRupiah(summary.drawer_expenses), spending: formatRupiah(summary.shopping_fund_used), other: formatRupiah(summary.other_fund_expenses) })}
		value={formatRupiah(Number(summary.drawer_expenses) + Number(summary.shopping_fund_used) + Number(summary.other_fund_expenses))}
		icon="shopping-bag"
		accent="accent"
	/>
	<SummaryCard
		label={termText.difference}
		caption={format(mutationText.differencesBreakdown, { float: formatSigned(summary.float_difference), spending: formatSigned(summary.shopping_difference), revenue: formatSigned(summary.revenue_difference) })}
		value={formatSigned(differences.reduce((total, value) => total + value, 0))}
		icon="scale"
		accent={differences.some((value) => value < 0) ? 'red' : 'plain'}
	/>
</div>

<Card flush>
	<CardHeader divided title={mutationText.listTitle} description={mutationText.listDescription} />
	{#if data.items.length === 0}
		<Notice text={mutationText.noSessions} />
	{:else}
		<DataTable {columns} rows={data.items} rowKey={(row) => row.session_id} trailing="selisih" loading={mutations.loading} sort={mutations.sort} onopen={(row) => void goto(mutationPath(row.session_id))}>
			{#snippet first(row)}
				<span class="block">{row.cashier_username}</span>
				<span class="block text-xs font-normal text-slate-500">{row.shift_code ?? EMPTY_VALUE}</span>
			{/snippet}
		</DataTable>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={data.page} total={data.total} unit="sesi" disabled={mutations.loading} onchange={(page) => mutations.setPage(page)} />
		</div>
	{/if}
</Card>
