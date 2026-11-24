<script lang="ts">
	import PrimaryButton from '$lib/components/button/PrimaryButton.svelte';
	import ListRow from '$lib/components/card/ListRow.svelte';
	import FailureState from '$lib/components/feedback/FailureState.svelte';
	import LoadingState from '$lib/components/feedback/LoadingState.svelte';
	import SectionTitle from '$lib/components/feedback/SectionTitle.svelte';
	import StatusBadge from '$lib/components/feedback/StatusBadge.svelte';
	import PagedListCard from '$lib/components/pagination/PagedListCard.svelte';
	import ConfirmSheet from '$lib/components/sheet/ConfirmSheet.svelte';
	import { current } from '$lib/auth/current.svelte';
	import type { DaySegment } from '$lib/features/dayplan/dayplan.svelte';
	import { durationLabel, timeRange, whenLabel } from '$lib/format/labels';
	import { t } from '$lib/text/t';
	import { OvertimeState } from '../overtime.svelte';
	import { Permission } from '$lib/auth/permissions';
	import { can } from '$lib/auth/session';
	import OvertimeFormSheet from './OvertimeFormSheet.svelte';

	/** Bagian lembur karyawan, disisipkan ke halaman yang membutuhkannya. */
	let { scheduledOvertime, onRecorded, onSessionExpired }: { scheduledOvertime: DaySegment | null; onRecorded: () => void; onSessionExpired: () => void } = $props();

	const overtime = new OvertimeState(() => onSessionExpired());

	$effect(() => {
		void overtime.load();
	});

	// Dimuat setiap halaman tampil dan setiap app kembali dari latar belakang, agar data tidak basi.
	$effect(() => {
		const reload = () => document.visibilityState === 'visible' && void overtime.load();
		document.addEventListener('visibilitychange', reload);
		return () => document.removeEventListener('visibilitychange', reload);
	});

	let noticing = $state(false);
	let recording = $state(false);

	const user = $derived(current.session?.user);
	const canRecord = $derived(user ? can(user, Permission.OvertimeSelf) : false);
</script>

{#if noticing}
	<ConfirmSheet
		title={t('overtime_unplanned_title')}
		message={scheduledOvertime ? t('overtime_unplanned_blocked', timeRange(scheduledOvertime.start.time, scheduledOvertime.end.time)) : t('overtime_unplanned_message')}
		confirmLabel={t('overtime_unplanned_continue')}
		dismissLabel={t('overtime_unplanned_back')}
		confirmEnabled={scheduledOvertime === null}
		onConfirm={() => {
			noticing = false;
			recording = true;
		}}
		onDismiss={() => (noticing = false)}
	/>
{/if}

{#if recording}
	<OvertimeFormSheet
		submitting={overtime.working}
		error={overtime.error}
		onSubmit={async (request) => {
			if (await overtime.record(request)) {
				recording = false;
				onRecorded();
			}
		}}
		onDismiss={() => {
			overtime.clearError();
			recording = false;
		}}
	/>
{/if}

<div class="flex w-full flex-col gap-3">
	<SectionTitle text={t('overtime_title')} />
	{#if canRecord}
		<PrimaryButton text={t('overtime_start')} onclick={() => (noticing = true)} />
	{/if}
	{#if overtime.loading}
		<LoadingState rows={2} />
	{:else if overtime.failure}
		<FailureState failure={overtime.failure} onRetry={() => void overtime.load()} />
	{:else}
		<SectionTitle text={t('overtime_history')} />
		<PagedListCard items={overtime.pageEntries} page={overtime.page} pageCount={overtime.pageCount} onPageChange={(page) => overtime.setPage(page)} emptyText={t('overtime_empty')}>
			{#snippet row(entry)}
				<ListRow
					title={entry.start ? whenLabel(entry.start) : ''}
					detail={entry.start && entry.end ? timeRange(entry.start.time, entry.end.time) : null}
					caption={entry.note}
					footnote={entry.scheduled ? t('overtime_kind_scheduled') : t('overtime_kind_unplanned')}
				>
					{#snippet trailing()}<StatusBadge text={durationLabel(entry.minutes)} tone="positive" />{/snippet}
				</ListRow>
			{/snippet}
		</PagedListCard>
	{/if}
</div>
