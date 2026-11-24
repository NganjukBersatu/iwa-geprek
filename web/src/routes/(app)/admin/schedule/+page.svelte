<script lang="ts">
	import { goto } from '$app/navigation';
	import { scheduleBulkPath } from '$lib/nav/pages';
	import Button from '$lib/components/button/Button.svelte';
	import MoreButton from '$lib/components/button/MoreButton.svelte';
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import ScheduleView from '$lib/features/schedule/components/ScheduleView.svelte';
	import { ScheduleState } from '$lib/features/schedule/schedule.svelte';
	import { pageText } from '$lib/text/pages';

	const schedule = new ScheduleState();
</script>

<ManageShell
	manage={schedule}
	filters={schedule.filters}
	title={pageText.scheduleTitle}
	description={pageText.scheduleDescription}
	loadingText="Memuat jadwal..."
>
	{#snippet actions()}
		{#if schedule.canArrange}
			<Button label={pageText.bulkEntry} icon="list-details" compact onclick={() => void goto(scheduleBulkPath())} />
			<MoreButton selection={schedule.selection} />
		{/if}
	{/snippet}
	{#snippet children()}
		<ScheduleView {schedule} />
	{/snippet}
</ManageShell>
