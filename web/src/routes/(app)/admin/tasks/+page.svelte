<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { access } from '$lib/auth/access.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Tabs from '$lib/components/tabs/Tabs.svelte';
	import { BatchesState } from '$lib/features/batches/batches.svelte';
	import BatchesView from '$lib/features/batches/components/BatchesView.svelte';
	import BatchRunsView from '$lib/features/batches/components/BatchRunsView.svelte';
	import TasksGuide from '$lib/features/batches/components/TasksGuide.svelte';
	import { RunsState } from '$lib/features/batches/runs.svelte';
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import TasksView from '$lib/features/tasks/components/TasksView.svelte';
	import { TasksState } from '$lib/features/tasks/tasks.svelte';
	import { live } from '$lib/live/live';
	import { enter } from '$lib/motion/transitions';
	import { batchNewPath, taskNewPath, TASKS_TAB_PARAM } from '$lib/nav/pages';
	import { memoryKey, recall, remember } from '$lib/stores/memory';
	import { whenChanged } from '$lib/stores/when-changed.svelte';
	import { batchRunText } from '$lib/text/batch-runs';
	import { batchText } from '$lib/text/batches';
	import { pageText } from '$lib/text/pages';

	const GUIDE_ID = 'tasks';
	const GUIDE_SEEN = 'dilihat';
	const TABS = ['employee', 'routine', 'outlet', 'history'];

	const tasks = new TasksState();
	const routines = new BatchesState('routine');
	const batches = new BatchesState('outlet');
	const runs = new RunsState();

	const fromAddress = page.url.searchParams.get(TASKS_TAB_PARAM) ?? '';
	let tab = $state(TABS.includes(fromAddress) ? fromAddress : 'employee');
	// The guide opens by itself once, then only from its button.
	let guideOpen = $state(recall(memoryKey.guide(GUIDE_ID)) !== GUIDE_SEEN);

	function showGuide(open: boolean): void {
		guideOpen = open;
		if (!open) remember(memoryKey.guide(GUIDE_ID), GUIDE_SEEN);
	}

	const tabs = $derived([
		{ key: 'employee', label: pageText.employeeTasks, count: tasks.loaded ? tasks.total : undefined },
		{ key: 'routine', label: batchRunText.tabRoutine, count: routines.loaded ? routines.total : undefined },
		{ key: 'outlet', label: pageText.outletTasks, count: batches.loaded ? batches.total : undefined },
		{ key: 'history', label: batchRunText.tabHistory, count: runs.loaded ? runs.total : undefined }
	]);

	const filters = $derived(tab === 'routine' ? routines.filters : tab === 'outlet' ? batches.filters : tab === 'history' ? runs.filters : tasks.filters);
	const canManage = $derived(access.allows('manage_tasks'));

	whenChanged(() => routines.query, () => void routines.queryChanged());
	whenChanged(() => batches.query, () => void batches.queryChanged());
	whenChanged(() => runs.query, () => void runs.queryChanged());
	onMount(() => {
		const offRoutines = live.on(routines.tables, () => void routines.refresh());
		const offBatches = live.on(batches.tables, () => void batches.refresh());
		const offRuns = live.on(runs.tables, () => void runs.refresh());
		return () => {
			offRoutines();
			offBatches();
			offRuns();
		};
	});
</script>

<ManageShell manage={tasks} {filters} title={pageText.tasksTitle} description={batchRunText.tasksDescription} loadingText={batchRunText.tasksLoading}>
	{#snippet actions()}
		<Button label={batchRunText.guide} icon="help-circle" compact onclick={() => showGuide(true)} />
		{#if tab === 'routine'}
			{#if canManage}
				<Button label={batchText.kinds.routine.add} icon="plus" variant="primary" compact onclick={() => void goto(batchNewPath('routine'))} />
			{/if}
		{:else if tab === 'outlet'}
			{#if canManage}
				<Button label={batchText.kinds.outlet.add} icon="plus" variant="primary" compact onclick={() => void goto(batchNewPath('outlet'))} />
			{/if}
		{:else if tab === 'employee'}
			<Button label={pageText.addTask} icon="plus" variant="primary" compact onclick={() => void goto(taskNewPath())} />
		{/if}
	{/snippet}
	{#snippet children()}
		<Tabs {tabs} label={batchRunText.taskKind} bind:value={tab} class="-mt-2" />
		{#key tab}
			<div in:enter>
				{#if tab === 'routine'}
					<BatchesView batches={routines} />
				{:else if tab === 'outlet'}
					<BatchesView {batches} />
				{:else if tab === 'history'}
					<BatchRunsView {runs} />
				{:else}
					<TasksView {tasks} />
				{/if}
			</div>
		{/key}
	{/snippet}
</ManageShell>

<TasksGuide open={guideOpen} onclose={() => showGuide(false)} />
