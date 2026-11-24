<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import PrimaryButton from '$lib/components/button/PrimaryButton.svelte';
	import DetailRow from '$lib/components/card/DetailRow.svelte';
	import Divider from '$lib/components/feedback/Divider.svelte';
	import ListCard from '$lib/components/card/ListCard.svelte';
	import ShiftRow from '$lib/components/card/ShiftRow.svelte';
	import FailureState from '$lib/components/feedback/FailureState.svelte';
	import LoadingState from '$lib/components/feedback/LoadingState.svelte';
	import Notice from '$lib/components/feedback/Notice.svelte';
	import SectionTitle from '$lib/components/feedback/SectionTitle.svelte';
	import StatusBadge from '$lib/components/feedback/StatusBadge.svelte';
	import PhotoPair from '$lib/components/media/PhotoPair.svelte';
	import AppText from '$lib/components/text/AppText.svelte';
	import { current } from '$lib/auth/current.svelte';
	import { displayName } from '$lib/auth/session';
	import { DayPlanState } from '$lib/features/dayplan/dayplan.svelte';
	import { SelfScheduleState } from '$lib/features/selfschedule/selfschedule.svelte';
	import SelfScheduleSheets from '$lib/features/selfschedule/SelfScheduleSheets.svelte';
	import PairingSection from '$lib/features/pairing/PairingSection.svelte';
	import { whenLabel, timeRange } from '$lib/format/labels';
	import { parseHexColor } from '$lib/theme/hex';
	import { t } from '$lib/text/t';
	import { AttendanceScreenState } from '../attendance.svelte';
	import type { AttendanceRecord, ClockInBlock, ScheduleSummary } from '../models';
	import AutoCloseNotices from './AutoCloseNotices.svelte';
	import ClockCelebration from './ClockCelebration.svelte';
	import ClockSheet from './ClockSheet.svelte';
	import PhasePanel from './PhasePanel.svelte';

	const NO_VALUE = '—';

	/** Halaman Absen: panel fase, jadwal, status, tombol absen, foto datang dan pulang, lalu penautan perangkat operasional. */
	let { onSessionExpired }: { onSessionExpired: () => void } = $props();

	const attendance = new AttendanceScreenState(() => onSessionExpired());
	const dayPlan = new DayPlanState();
	const selfSchedule = new SelfScheduleState(() => onSessionExpired());

	$effect(() => {
		void attendance.load();
		void dayPlan.load(onSessionExpired);
	});

	// Dimuat ulang setiap app kembali dari latar belakang, agar status tidak basi.
	$effect(() => {
		const reload = () => {
			if (document.visibilityState !== 'visible') return;
			void attendance.load();
			void dayPlan.load(onSessionExpired);
		};
		document.addEventListener('visibilitychange', reload);
		return () => document.removeEventListener('visibilitychange', reload);
	});

	const state = $derived(attendance.state);
	const userName = $derived(current.session ? displayName(current.session.user) : '');
	const clockedIn = $derived(state?.record ? state.record.clockIn !== null && state.record.clockOut === null : false);

	/** Kode shift bila ada, selain itu rentang jamnya. */
	function rangeOf(schedule: ScheduleSummary): string {
		const start = schedule.startsAt?.time;
		const end = schedule.endsAt?.time;
		return start && end ? timeRange(start, end) : '';
	}

	function blockText(block: ClockInBlock | null): string {
		const schedule = block?.schedule ? (block.schedule.code ?? rangeOf(block.schedule)) : '';
		const at = block?.at ? whenLabel(block.at) : '';
		switch (block?.reason) {
			case 'not-open-yet':
				return t('attendance_block_not_open_yet', schedule, at);
			case 'already-used':
				return t('attendance_block_already_used', schedule);
			case 'ended':
				return t('attendance_block_ended', schedule, at);
			case 'no-permission':
				return t('attendance_block_no_permission');
			default:
				return t('attendance_block_no_schedule');
		}
	}

	function statusOf(record: AttendanceRecord | null): [string, 'positive' | 'neutral'] {
		if (record?.clockOut) return [t('attendance_status_out'), 'positive'];
		if (record?.clockIn) return [t('attendance_status_in'), 'positive'];
		return [t('attendance_status_none'), 'neutral'];
	}
</script>

{#snippet scheduleCard(schedule: ScheduleSummary | null)}
	<ListCard>
		{#if schedule === null}
			<Notice text={t('attendance_no_schedule')} />
		{:else}
			<ShiftRow title={rangeOf(schedule)} code={schedule.code} codeColor={parseHexColor(schedule.colorHex)} />
		{/if}
	</ListCard>
{/snippet}

{#snippet statusCard(record: AttendanceRecord | null)}
	{@const [label, tone] = statusOf(record)}
	<ListCard>
		<DetailRow label={t('attendance_detail_status')}>
			{#snippet valueContent()}
				<span class="flex items-center gap-2">
					<StatusBadge text={label} {tone} />
					{#if record?.late}<StatusBadge text={t('attendance_late_badge')} tone="warning" />{/if}
				</span>
			{/snippet}
		</DetailRow>
		<Divider />
		<DetailRow label={t('attendance_clock_in')} value={record?.clockIn ? whenLabel(record.clockIn) : NO_VALUE} />
		<Divider />
		<DetailRow label={t('attendance_clock_out')}>
			{#snippet valueContent()}
				<span class="flex items-center gap-2">
					<AppText role="body">{record?.clockOut ? whenLabel(record.clockOut) : NO_VALUE}</AppText>
					{#if record?.autoClosed}<StatusBadge text={t('attendance_detail_auto_closed')} tone="warning" />{/if}
				</span>
			{/snippet}
		</DetailRow>
	</ListCard>
{/snippet}

<SelfScheduleSheets state={selfSchedule} onCreated={(scheduleId) => attendance.startSelfScheduled(scheduleId)} />

{#if attendance.sheet}
	<ClockSheet
		kind={attendance.sheet}
		submitting={attendance.submitting}
		submitError={attendance.submitError}
		onSubmit={(photo, outside, note) => void attendance.submit(photo, outside, note, userName)}
		onDismiss={() => attendance.closeSheet()}
		notice={attendance.selfScheduledId ? t('self_schedule_saved') : null}
		branch={state?.branch ?? null}
		distance={attendance.previewDistance}
		locating={attendance.locating}
		located={attendance.preview !== null || !attendance.locating}
		locationProblem={attendance.locationProblem}
		onRelocate={() => void attendance.locate()}
	/>
{/if}
{#if attendance.celebration}
	<ClockCelebration celebration={attendance.celebration} onDone={() => attendance.finishCelebration()} />
{/if}

<div class="flex h-full w-full justify-center overflow-y-auto">
	<div class="w-full max-w-[var(--size-content-max)]" use:dynamicStyle={{ padding: '16px var(--page-padding)' }}>
		{#if attendance.loading}
			<LoadingState />
		{:else if attendance.failure || !state}
			<FailureState failure={attendance.failure ?? { kind: 'unexpected', type: 'Data kosong', where: 'status' }} onRetry={() => void attendance.load()} />
		{:else}
			{#if state.notices.length > 0}
				<AutoCloseNotices notices={state.notices} acknowledging={attendance.acknowledging} onAcknowledge={() => void attendance.acknowledgeNotices()} />
			{/if}

			<PhasePanel segments={dayPlan.segments} {clockedIn} />

			<SectionTitle text={t('attendance_today_schedule')} />
			{@render scheduleCard(state.schedule)}

			<div class="pt-3">{@render statusCard(state.record)}</div>

			<div class="pt-3">
				{#if state.canClockOut}
					<PrimaryButton text={t('attendance_action_out')} onclick={() => attendance.openSheet('out')} container="accent" content="content" />
				{:else if state.canClockIn}
					<PrimaryButton text={t('attendance_action_in')} onclick={() => attendance.openSheet('in')} />
				{:else if state.canSelfSchedule}
					<!-- Tanpa jadwal hari ini, absen datang tetap tersedia dan dimulai dengan absen mandiri. -->
					<PrimaryButton text={t('attendance_action_in')} onclick={() => selfSchedule.start()} />
				{:else}
					<Notice text={blockText(state.clockInBlock)} />
				{/if}
			</div>

			<div class="pt-6">
				<PhotoPair
					first={{ url: state.record?.photoInUrl ?? null, caption: t('attendance_detail_photo_in') }}
					second={{ url: state.record?.photoOutUrl ?? null, caption: t('attendance_detail_photo_out') }}
				/>
			</div>
		{/if}
		<PairingSection {onSessionExpired} />
	</div>
</div>
