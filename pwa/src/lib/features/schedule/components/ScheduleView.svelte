<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import DividedItems from '$lib/components/card/DividedItems.svelte';
	import StateListCard from '$lib/components/card/StateListCard.svelte';
	import MonthCalendar from '$lib/components/calendar/MonthCalendar.svelte';
	import CodeLegendTrigger from '$lib/components/calendar/CodeLegendTrigger.svelte';
	import type { CodeLegendItem } from '$lib/components/calendar/types';
	import ToggleSwitch from '$lib/components/field/ToggleSwitch.svelte';
	import FailureState from '$lib/components/feedback/FailureState.svelte';
	import SectionTitle from '$lib/components/feedback/SectionTitle.svelte';
	import { weekdayDateLabel, timeRange, monthYearLabel } from '$lib/format/labels';
	import { parseHexColor } from '$lib/theme/hex';
	import { t, tArray } from '$lib/text/t';
	import { ScheduleState } from '../schedule.svelte';
	import ScheduleRow from './ScheduleRow.svelte';

	let { onSessionExpired }: { onSessionExpired: () => void } = $props();

	const schedule = new ScheduleState(() => onSessionExpired());

	$effect(() => {
		void schedule.load();
	});

	// Dimuat ulang setiap app kembali dari latar belakang, agar jadwal tidak basi.
	$effect(() => {
		const reload = () => document.visibilityState === 'visible' && void schedule.load();
		document.addEventListener('visibilitychange', reload);
		return () => document.removeEventListener('visibilitychange', reload);
	});

	const legend = $derived<CodeLegendItem[]>(
		schedule.codes.map((code) => {
			const hours = code.off || !code.start || !code.end ? t('schedule_day_off') : timeRange(code.start, code.end);
			const overtime = code.overtimeStart && code.overtimeEnd ? t('schedule_overtime', timeRange(code.overtimeStart, code.overtimeEnd)) : null;
			return { code: code.code, color: parseHexColor(code.color), title: code.category ?? hours, detail: code.category ? hours : null, caption: overtime };
		})
	);
</script>

<div class="flex h-full w-full justify-center overflow-y-auto">
	<div class="flex w-full max-w-[var(--size-content-max)] flex-col gap-1" use:dynamicStyle={{ padding: '16px var(--page-padding)' }}>
		<div class="flex w-full items-center justify-between">
			{#if schedule.outletName}
				<div class="flex-1"><SectionTitle text={t('schedule_outlet', schedule.outletName)} padded={false} /></div>
			{:else}
				<div class="flex-1"></div>
			{/if}
			<ToggleSwitch label={t('schedule_only_mine')} checked={schedule.onlyMine} onchange={() => schedule.toggleOnlyMine()} />
		</div>

		<MonthCalendar
			month={schedule.month}
			monthLabel={monthYearLabel(schedule.month)}
			weekdayLabels={tArray('weekdays_short')}
			selected={schedule.selected}
			today={schedule.today}
			markers={schedule.markers}
			fills={schedule.fills}
			pulses={schedule.pulses}
			onSelect={(date) => schedule.select(date)}
			onPrevious={() => schedule.previousMonth()}
			onNext={() => schedule.nextMonth()}
			nextEnabled={schedule.canGoNext && !schedule.loading}
		>
			{#snippet footer()}
				{#if legend.length > 0}<CodeLegendTrigger title={t('schedule_codes')} items={legend} />{/if}
			{/snippet}
		</MonthCalendar>

		<SectionTitle text={weekdayDateLabel(schedule.selected)} />
		{#if schedule.failure}
			<FailureState failure={schedule.failure} onRetry={() => void schedule.load()} />
		{:else}
			<StateListCard loading={schedule.loading} empty={schedule.dayItems.length === 0} emptyText={t('schedule_empty')}>
				<DividedItems items={schedule.dayItems}>
					{#snippet row(entry)}
						<ScheduleRow item={entry} showUser />
					{/snippet}
				</DividedItems>
			</StateListCard>
		{/if}
	</div>
</div>
