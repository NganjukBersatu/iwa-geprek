<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import DateBadge from '$lib/components/card/DateBadge.svelte';
	import DividedItems from '$lib/components/card/DividedItems.svelte';
	import ListCard from '$lib/components/card/ListCard.svelte';
	import ListRow from '$lib/components/card/ListRow.svelte';
	import StatCard from '$lib/components/card/StatCard.svelte';
	import StateListCard from '$lib/components/card/StateListCard.svelte';
	import MonthPicker from '$lib/components/calendar/MonthPicker.svelte';
	import ProgressRing from '$lib/components/chart/ProgressRing.svelte';
	import FailureState from '$lib/components/feedback/FailureState.svelte';
	import AppText from '$lib/components/text/AppText.svelte';
	import { clock, dayOfMonth, weekdayIndex } from '$lib/format/datetime';
	import { failureText } from '$lib/failure/failure';
	import { formatRupiah, monthYearLabel } from '$lib/format/labels';
	import { t, tArray } from '$lib/text/t';
	import { PresenceState, type AttendanceDay } from '../presence.svelte';
	import AttendanceDetailSheet from './AttendanceDetailSheet.svelte';
	import AttendanceStatusBadge from './AttendanceStatusBadge.svelte';

	const PERCENT_FULL = 100;
	const NO_TIME = '—';

	/** Halaman Kehadiran: ringkasan bulan, hitungan, potongan, dan hari-hari absen. */
	let { onSessionExpired }: { onSessionExpired: () => void } = $props();

	const presence = new PresenceState(() => onSessionExpired());

	$effect(() => {
		void presence.load(null);
	});

	// Dimuat setiap halaman tampil dan setiap app kembali dari latar belakang, agar data tidak basi.
	$effect(() => {
		const reload = () => document.visibilityState === 'visible' && presence.retry();
		document.addEventListener('visibilitychange', reload);
		return () => document.removeEventListener('visibilitychange', reload);
	});

	let selectedDay = $state<AttendanceDay | null>(null);

	const attendance = $derived(presence.attendance);
	const total = $derived(attendance ? attendance.present + attendance.notPresent : 0);
	const progress = $derived(attendance && total > 0 ? attendance.present / total : 0);
	const monthLabel = $derived(presence.month ? monthYearLabel(presence.month) : '');
	const heroLabel = $derived(presence.month ? t('dashboard_hero_label', tArray('months')[presence.month.month - 1] ?? '', String(presence.month.year)) : t('dashboard_section_attendance'));
	const heroValue = $derived(attendance ? t('dashboard_hero_value', String(attendance.present), String(total)) : t('dashboard_hero_empty'));
	const heroSub = $derived(presence.failure ? failureText(presence.failure) : attendance ? t('dashboard_hero_sub', String(attendance.late), String(attendance.notPresent)) : t('common_loading'));

	function timeOf(day: AttendanceDay): string {
		const clockIn = clock(day.clockIn);
		const clockOut = clock(day.clockOut);
		if (clockIn === null) return NO_TIME;
		return clockOut === null ? `${clockIn} –` : `${clockIn} – ${clockOut}`;
	}
</script>

{#if selectedDay}<AttendanceDetailSheet day={selectedDay} onDismiss={() => (selectedDay = null)} />{/if}

<div class="flex size-full justify-center overflow-y-auto" use:dynamicStyle={{ 'padding-inline': 'var(--page-padding)' }}>
	<div class="flex w-full max-w-[var(--size-content-max)] flex-col gap-2" use:dynamicStyle={{ 'padding-bottom': '24px' }}>
		<div class="flex w-full items-center gap-4 rounded-card bg-primary p-4">
			<ProgressRing {progress} label="{Math.round(progress * PERCENT_FULL)}%" trackColor="on-primary-subtle" indicatorColor="accent" labelColor="on-primary" />
			<div class="min-w-0 flex-1">
				<AppText role="caption" color="on-primary-muted">{heroLabel}</AppText>
				<AppText role="title" color="on-primary">{heroValue}</AppText>
				<AppText role="caption" color="on-primary-muted">{heroSub}</AppText>
			</div>
		</div>

		<MonthPicker label={monthLabel} onPrevious={() => presence.previousMonth()} onNext={() => presence.nextMonth()} nextEnabled={presence.canGoNext && !presence.loading} />

		{#if presence.failure}
			<ListCard><FailureState failure={presence.failure} onRetry={() => presence.retry()} /></ListCard>
		{:else}
			{#if attendance && attendance.days.length > 0 && !presence.loading}
				<div class="flex gap-2">
					<div class="min-w-0 flex-1"><StatCard label={t('dashboard_stat_present')} value={String(attendance.present)} /></div>
					<div class="min-w-0 flex-1"><StatCard label={t('dashboard_stat_late')} value={String(attendance.late)} /></div>
					<div class="min-w-0 flex-1"><StatCard label={t('dashboard_stat_not_present')} value={String(attendance.notPresent)} /></div>
				</div>
				<StatCard label={t('dashboard_stat_penalty')} value={formatRupiah(attendance.penalty)} valueColor={attendance.penalty > 0 ? 'danger' : 'content'} icon="Alert" iconBeside />
			{/if}
			<StateListCard loading={presence.loading} empty={!attendance || attendance.days.length === 0} emptyText={t('dashboard_empty_attendance')} skeletonRows={4}>
				<DividedItems items={attendance?.days ?? []}>
					{#snippet row(day)}
						<ListRow title={timeOf(day)} onclick={() => (selectedDay = day)}>
							{#snippet leading()}<DateBadge weekday={tArray('weekdays_short')[weekdayIndex(day.date)] ?? ''} day={dayOfMonth(day.date)} />{/snippet}
							{#snippet trailing()}<AttendanceStatusBadge {day} />{/snippet}
						</ListRow>
					{/snippet}
				</DividedItems>
			</StateListCard>
		{/if}
	</div>
</div>
