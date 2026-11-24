<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import type { VoidReport } from '$lib/api/types';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import SummaryCard from '$lib/components/card/SummaryCard.svelte';
	import Pager from '$lib/components/pager/Pager.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { formatNumber, formatPercentPlain, formatRupiah } from '$lib/format/currency';
	import type { VoidsState } from '../voids.svelte';
	import { voidColumns, voidOrderName } from '../columns';
	import { voidText } from '$lib/text/voids';
	import { format } from '$lib/text/format';

	let { data, voids }: { data: VoidReport; voids: VoidsState } = $props();

	const top = $derived(data.by_user[0]);

	const columns = voidColumns;
</script>

<div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
	<SummaryCard
		label={voidText.cancelled}
		caption={format(voidText.ofTransactions, { count: formatPercentPlain(data.void_percent ?? 0), total: formatNumber(data.valid_transactions + data.count, 0) })}
		value={format(controlText.transactionsCount, { count: formatNumber(data.count, 0) })}
		icon="receipt-off"
		accent="primary"
	/>
	<SummaryCard label={voidText.cancelledValue} caption={voidText.notInIncome} value={formatRupiah(data.total_value)} icon="wallet" accent="accent" />
	<SummaryCard
		label={voidText.mostFrequent}
		caption={data.by_user.map((person) => `${person.username} ${person.count}×`).join(' · ') || voidText.noCancellations}
		value={top?.username ?? '—'}
		icon="user-x"
		accent="ink"
	/>
</div>

<Card flush>
	<CardHeader divided title={voidText.listTitle} description={voidText.listDescription} />
	{#if data.orders.length === 0}
		<Notice text={voidText.noCancellationsInPeriod} />
	{:else}
		<DataTable sort={voids.sort} {columns} rows={data.orders} rowKey={(row) => row.order_id} trailing="total" loading={voids.loading}>
			{#snippet first(row)}
				<span class="block">{voidOrderName(row)}</span>
				<span class="block max-w-xs truncate text-xs font-normal text-slate-500">{row.items_summary}</span>
			{/snippet}
		</DataTable>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={data.page} total={data.count} unit="transaksi batal" disabled={voids.loading} onchange={(page) => voids.setPage(page)} />
		</div>
	{/if}
</Card>
