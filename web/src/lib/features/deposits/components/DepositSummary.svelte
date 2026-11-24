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
	// Dipegang dan disetor sama-sama nol berarti belum ada pendapatan, bukan sudah disetor semua.
	const noRevenue = $derived(summary !== null && Number(summary.held) === 0 && Number(summary.paid_total) === 0);
	const heldCaption = $derived.by(() => {
		if (open.length > 0 && summary?.oldest_open_day) {
			return format(depositText.openDaysSummary, { count: open.length, dates: rangesOf(open), days: daysAgo(summary.oldest_open_day) });
		}
		return noRevenue ? depositText.noRevenueYet : depositText.allDepositedTitle;
	});
</script>

{#if summary}
	<div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
		<SummaryCard label={depositText.stillHeld} caption={heldCaption} value={formatRupiah(summary.held)} icon="hand-stop" accent="plain" />
		<SummaryCard
			label={depositText.deposited}
			caption={summary.last_deposit_date ? format(depositText.depositsCountWithLast, { count: summary.deposit_count, date: formatDate(summary.last_deposit_date) }) : format(depositText.depositsCount, { count: summary.deposit_count })}
			value={formatRupiah(summary.paid_total)}
			icon="cash"
			accent="plain"
		/>
		{#if summary.deposit_count === 0}
			<SummaryCard label={depositText.receiptPhoto} caption={depositText.receiptAfterDeposit} value={depositText.noDepositYet} icon="receipt" accent="plain" />
		{:else}
			<SummaryCard
				label={depositText.receiptPhoto}
				caption={summary.without_photo > 0 ? depositText.openHistoryToComplete : depositText.allHaveReceipts}
				value={summary.without_photo > 0 ? format(depositText.withoutPhoto, { count: summary.without_photo }) : depositText.complete}
				icon="receipt"
				accent="plain"
				onclick={summary.without_photo > 0 ? () => (deposits.tab = 'riwayat') : undefined}
			/>
		{/if}
	</div>
{/if}
