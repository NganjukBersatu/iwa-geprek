<script lang="ts">
	import Badge from '$lib/components/card/Badge.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { formatDate } from '$lib/date/range';
	import { formatRupiah } from '$lib/format/currency';
	import { dayColumns, shareColumns } from '../columns';
	import type { DepositsState } from '../deposits.svelte';
	import { STATUS_TONE, rangesOf } from '../format';
	import { depositText } from '$lib/text/deposits';
	import { format } from '$lib/text/format';

	let { deposits }: { deposits: DepositsState } = $props();

	const shares = $derived(shareColumns((day) => deposits.dayOf(day)));
	const openRows = $derived(deposits.data?.open ?? []);
</script>

{#if deposits.loading && !deposits.data}
	<Notice text={depositText.loading} />
{:else}
	<div class="flex flex-col gap-4">
		<Card flush>
			<CardHeader divided title={format(depositText.notDepositedDays, { count: openRows.length })} description={openRows.length > 0 ? format(depositText.stillHeldAmount, { amount: formatRupiah(deposits.data?.summary.held ?? 0) }) : depositText.allDepositedInRange} />
			{#if openRows.length > 0}
				<DataTable sort={deposits.daySort} columns={dayColumns} rows={openRows} rowKey={(row) => row.day} selection={deposits.selection} onopen={(row) => (deposits.detail = { kind: 'day', id: row.day })} trailing="sisa">
					{#snippet cell(row, column)}
						{#if column.key === 'status'}<Badge tone={STATUS_TONE[row.status]}>{column.value(row)}</Badge>{:else}{column.value(row)}{/if}
					{/snippet}
				</DataTable>
			{/if}
		</Card>

		{#each deposits.deposits as deposit (deposit.id)}
			<Card flush>
				<CardHeader
					divided
					title={format(depositText.depositDateAmount, { date: formatDate(deposit.deposit_date), amount: formatRupiah(deposit.amount) })}
					description={format(depositText.closesDays, { days: rangesOf(deposit.days.map((share) => share.day)), branch: deposits.allBranches ? ` · ${deposit.outlet_name}` : '', photo: deposit.user_name ? ` · dicatat ${deposit.user_name}` : '', note: deposit.note ? ` · ${deposit.note}` : '' })}
				>
					{#snippet actions()}
						<Button label={deposit.photo_url ? depositText.receipt : depositText.noReceipt} icon={deposit.photo_url ? 'receipt' : 'photo-plus'} variant="tertiary" small compact onclick={() => (deposits.detail = { kind: 'deposit', id: deposit.id })} />
					{/snippet}
				</CardHeader>
				<DataTable sort={deposits.shareSort} columns={shares} rows={deposit.days} rowKey={(row) => row.day} onopen={(row) => (deposits.detail = { kind: 'day', id: row.day })} trailing="dialokasikan" />
			</Card>
		{:else}
			<Notice text={depositText.noDepositsInRange} />
		{/each}
	</div>
{/if}
