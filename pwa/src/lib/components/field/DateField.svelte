<script lang="ts">
	import MonthCalendar from '$lib/components/calendar/MonthCalendar.svelte';
	import BottomSheet from '$lib/components/sheet/BottomSheet.svelte';
	import { monthOf, nextMonth, previousMonth, type YearMonth } from '$lib/format/datetime';
	import { longDateLabel, monthYearLabel } from '$lib/format/labels';
	import { tArray } from '$lib/text/t';
	import PickerField from './PickerField.svelte';

	/** Isian tanggal berformat "YYYY-MM-DD" yang tampil seperti kolom teks dan membuka kalender bulan di lembar bawah saat diketuk. */
	let { label, value, today, onchange, enabled = true }: { label: string; value: string; today: string; onchange: (date: string) => void; enabled?: boolean } = $props();

	let open = $state(false);
	let month = $state<YearMonth>({ year: 0, month: 1 });

	// Kalender selalu dibuka di bulan nilai yang sedang dipilih.
	$effect(() => {
		month = monthOf(value);
	});
</script>

<PickerField {label} valueText={longDateLabel(value)} icon="Calendar" {enabled} onclick={() => (open = true)} />

{#if open}
	<BottomSheet title={label} onDismiss={() => (open = false)}>
		<MonthCalendar
			{month}
			monthLabel={monthYearLabel(month)}
			weekdayLabels={tArray('weekdays_short')}
			selected={value}
			{today}
			markers={{}}
			fills={{}}
			onSelect={(date) => {
				onchange(date);
				open = false;
			}}
			onPrevious={() => (month = previousMonth(month))}
			onNext={() => (month = nextMonth(month))}
			nextEnabled
		/>
	</BottomSheet>
{/if}
