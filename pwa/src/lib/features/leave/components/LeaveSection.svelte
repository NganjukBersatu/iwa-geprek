<script lang="ts">
	import PrimaryButton from '$lib/components/button/PrimaryButton.svelte';
	import DividedItems from '$lib/components/card/DividedItems.svelte';
	import ListRow from '$lib/components/card/ListRow.svelte';
	import StateListCard from '$lib/components/card/StateListCard.svelte';
	import FailureState from '$lib/components/feedback/FailureState.svelte';
	import SectionTitle from '$lib/components/feedback/SectionTitle.svelte';
	import StatusBadge from '$lib/components/feedback/StatusBadge.svelte';
	import { t } from '$lib/text/t';
	import { LeaveState, leaveRangeLabel, leaveStatusLabel, leaveStatusTone, leaveTypeLabel, type LeaveRequest } from '../leave.svelte';
	import LeaveDetailSheet from './LeaveDetailSheet.svelte';
	import LeaveRequestSheet from './LeaveRequestSheet.svelte';

	/** Bagian pengajuan izin karyawan, disisipkan ke halaman yang membutuhkannya. */
	let { onSessionExpired }: { onSessionExpired: () => void } = $props();

	const leave = new LeaveState(() => onSessionExpired());

	$effect(() => {
		void leave.load();
	});

	// Dimuat setiap halaman tampil dan setiap app kembali dari latar belakang, agar data tidak basi.
	$effect(() => {
		const reload = () => document.visibilityState === 'visible' && void leave.load();
		document.addEventListener('visibilitychange', reload);
		return () => document.removeEventListener('visibilitychange', reload);
	});

	let requesting = $state(false);
	let selected = $state<LeaveRequest | null>(null);
</script>

{#if requesting}
	<LeaveRequestSheet
		submitting={leave.working}
		error={leave.error}
		onSubmit={async (form, attachment) => {
			if (await leave.submit(form, attachment)) requesting = false;
		}}
		onDismiss={() => {
			leave.clearError();
			requesting = false;
		}}
	/>
{/if}

{#if selected}
	<LeaveDetailSheet
		request={selected}
		working={leave.working}
		error={leave.error}
		onCancel={async () => {
			if (selected && (await leave.cancel(selected.id))) selected = null;
		}}
		onDismiss={() => {
			leave.clearError();
			selected = null;
		}}
	/>
{/if}

<div class="flex w-full flex-col gap-3">
	<SectionTitle text={t('leave_title')} />
	<PrimaryButton text={t('leave_action')} onclick={() => (requesting = true)} />
	{#if leave.failure}
		<FailureState failure={leave.failure} onRetry={() => void leave.load()} />
	{:else}
		<StateListCard loading={leave.loading} empty={leave.items.length === 0} emptyText={t('leave_empty')}>
			<DividedItems items={leave.items}>
				{#snippet row(request)}
					<ListRow title={leaveTypeLabel(request.type)} detail={leaveRangeLabel(request)} caption={request.reason} onclick={() => (selected = request)}>
						{#snippet trailing()}<StatusBadge text={leaveStatusLabel(request.status)} tone={leaveStatusTone(request.status)} />{/snippet}
					</ListRow>
				{/snippet}
			</DividedItems>
		</StateListCard>
	{/if}
</div>
