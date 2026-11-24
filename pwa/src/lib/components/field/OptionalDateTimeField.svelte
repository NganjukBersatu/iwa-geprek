<script lang="ts">
	import { stampAt, todayWib } from '$lib/format/datetime';
	import { ServerClock } from '$lib/time/server-clock';
	import DateField from './DateField.svelte';
	import TimeField from './TimeField.svelte';
	import ToggleSwitch from './ToggleSwitch.svelte';
	import type { DateTimeValue } from './types';

	const DEFAULT_LEAD_SECONDS = 3600;

	/** Isian tanggal dan jam yang boleh dikosongkan lewat saklar, kecuali [removable] false dan nilainya sudah ada. */
	let {
		toggleLabel,
		dateLabel,
		timeLabel,
		value,
		onchange,
		enabled = true,
		removable = true
	}: {
		toggleLabel: string;
		dateLabel: string;
		timeLabel: string;
		value: DateTimeValue | null;
		onchange: (value: DateTimeValue | null) => void;
		enabled?: boolean;
		removable?: boolean;
	} = $props();

	const today = todayWib(ServerClock.nowEpochSeconds());

	function defaultValue(): DateTimeValue {
		const stamp = stampAt(ServerClock.nowEpochSeconds() + DEFAULT_LEAD_SECONDS);
		return { date: stamp.date, time: stamp.time };
	}
</script>

<div class="flex w-full flex-col gap-3">
	{#if removable || value === null}
		<ToggleSwitch label={toggleLabel} checked={value !== null} onchange={(on) => enabled && onchange(on ? defaultValue() : null)} />
	{/if}
	{#if value}
		{@const current = value}
		<DateField label={dateLabel} value={current.date} {today} {enabled} onchange={(date) => onchange({ date, time: current.time })} />
		<TimeField label={timeLabel} value={current.time} {enabled} onchange={(time) => onchange({ date: current.date, time })} />
	{/if}
</div>
