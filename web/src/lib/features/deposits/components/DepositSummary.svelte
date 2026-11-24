<script lang="ts">
	import SummaryCard from '$lib/components/card/SummaryCard.svelte';
	import { formatDate } from '$lib/date/range';
	import { formatRupiah } from '$lib/format/currency';
	import type { DepositsState } from '../deposits.svelte';
	import { daysAgo, rangesOf } from '../format';
	import { depositText } from '$lib/text/deposits';
	import { format } from '$lib/text/format';

	let { deposits }: { deposits: DepositsState } = $props();

	const summary = $derived(deposits.data?.summary ?? null);
	const open = $derived(deposits.openDays);
	const heldCaption = $derived(
		open.length > 0 && summary?.oldest_open_day
			? format(depositText.openDaysSummary, { count: open.length, dates: rangesOf(open), days: daysAgo(summary.oldest_open_day) })
			: depositText.allDepositedTitle
	);
</script>

{#if summary}
	<div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
		<SummaryCard label={depositText.stillHeld} caption={heldCaption} value={formatRupiah(summary.held)} icon="hand-stop" accent="plain" />
		<SummaryCard
			label={depositText.deposited}
			caption={format(depositText.depositsCount, { count: summary.deposit_count, last: summary.last_deposit_date ? ` · terakhir ${formatDate(summary.last_deposit_date)}` : '' })}
			value={formatRupiah(summary.paid_total)}
			icon="cash"
			accent="plain"
		/>
		<SummaryCard
			label={depositText.receiptPhoto}
			caption={summary.without_photo > 0 ? depositText.openHistoryToComplete : depositText.allHaveReceipts}
			value={summary.without_photo > 0 ? format(depositText.withoutPhoto, { count: summary.without_photo }) : depositText.complete}
			icon="receipt"
			accent="plain"
			onclick={summary.without_photo > 0 ? () => (deposits.tab = 'riwayat') : undefined}
		/>
	</div>
{/if}
