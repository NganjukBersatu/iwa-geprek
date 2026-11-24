<script lang="ts">
	import DateField from './DateField.svelte';

	/** Pasangan tanggal awal dan akhir ("YYYY-MM-DD"); rentang tidak pernah terbalik: memilih awal setelah akhir menggeser akhir, dan memilih akhir sebelum awal menggeser awal. */
	let {
		from,
		to,
		today,
		fromLabel,
		toLabel,
		onchange,
		enabled = true,
		sideBySide = false
	}: { from: string; to: string; today: string; fromLabel: string; toLabel: string; onchange: (from: string, to: string) => void; enabled?: boolean; sideBySide?: boolean } = $props();
</script>

<div class="flex w-full {sideBySide ? 'flex-row gap-2' : 'flex-col gap-3'}">
	<div class="min-w-0 flex-1"><DateField label={fromLabel} value={from} {today} {enabled} onchange={(date) => onchange(date, to < date ? date : to)} /></div>
	<div class="min-w-0 flex-1"><DateField label={toLabel} value={to} {today} {enabled} onchange={(date) => onchange(from > date ? date : from, date)} /></div>
</div>
