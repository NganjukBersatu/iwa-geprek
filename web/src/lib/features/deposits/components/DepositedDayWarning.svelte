<script lang="ts">
	import Banner from '$lib/components/card/Banner.svelte';
	import { formatDate } from '$lib/date/range';
	import { formatRupiah } from '$lib/format/currency';
	import type { DayWarning } from '../day-warning.svelte';
	import { depositText } from '$lib/text/deposits';
	import { format } from '$lib/text/format';

	/** `change` warns before money of a handed-over day changes; `deposit` warns before a day still running is handed over. */
	let { warning, mode = 'change' }: { warning: DayWarning; mode?: 'change' | 'deposit' } = $props();

	const days = $derived(mode === 'change' ? warning.deposited : warning.unfinished);
	const dates = $derived(days.map((day) => formatDate(day.day)).join(', '));
</script>

{#if warning.failed}
	<div class="mt-3">
		<Banner tone="warning" icon="alert-triangle" title={depositText.statusUnavailableTitle}>
			{depositText.statusUnavailableHint}
		</Banner>
	</div>
{:else if days.length > 0 && mode === 'change'}
	<div class="mt-3">
		<Banner tone="warning" icon="alert-triangle" title={days.length === 1 ? depositText.dayDepositedTitle : depositText.daysDepositedTitle}>
			{#each days as day (`${day.outlet_id}:${day.day}`)}
				<span class="block">{format(depositText.depositAlreadyRecorded, { date: formatDate(day.day), amount: formatRupiah(day.deposited) })}</span>
			{/each}
			{depositText.changeWarning}
		</Banner>
	</div>
{:else if days.length > 0}
	<div class="mt-3">
		<Banner tone="warning" icon="alert-triangle" title={depositText.sessionRunningTitle}>
			{format(depositText.sessionRunningNote, { dates: dates })}
		</Banner>
	</div>
{/if}
