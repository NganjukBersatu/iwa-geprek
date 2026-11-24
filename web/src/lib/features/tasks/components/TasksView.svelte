<script lang="ts">
	import { goto } from '$app/navigation';
	import { taskPath } from '$lib/nav/pages';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import ListSearch from '$lib/components/filter/ListSearch.svelte';
	import { noMatchText } from '$lib/components/filter/no-match';
	import Notice from '$lib/components/card/Notice.svelte';
	import Pager from '$lib/components/pager/Pager.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import Tabs from '$lib/components/tabs/Tabs.svelte';
	import { isLate } from '../display';
	import { STATUS_DONE, STATUS_OPEN, type TasksState } from '../tasks.svelte';
	import { taskColumns } from '../columns';
	import { taskText } from '$lib/text/tasks';

	let { tasks }: { tasks: TasksState } = $props();

	const tabs = [
		{ key: STATUS_OPEN, label: taskText.notDone },
		{ key: STATUS_DONE, label: taskText.done }
	];

	const done = $derived(tasks.status === STATUS_DONE);
	const columns = $derived(taskColumns(done));
</script>

<Card flush>
	<CardHeader divided title={taskText.listTitle} description={taskText.listDescription} />
	<ListSearch value={tasks.search} placeholder={taskText.searchPlaceholder} label={taskText.search} onsearch={(query) => tasks.setSearch(query)} />
	<Tabs {tabs} label={taskText.taskStatus} bind:value={tasks.status} />
	{#if !tasks.loading && tasks.items.length === 0}
		<Notice text={noMatchText('tugas', tasks.search !== '', tasks.filters.count > 0) ?? (done ? taskText.noDoneTasks : taskText.noPendingTasks)} />
	{:else}
		<DataTable sort={tasks.sort} {columns} rows={tasks.items} rowKey={(row) => row.id} loading={tasks.loading} trailing="waktu" onopen={(row) => void goto(taskPath(row.id))}>
			{#snippet first(row)}
				<span class="inline-flex items-center gap-2">
					<span>{row.title}</span>
					{#if isLate(row)}<Badge tone="danger">{taskText.overdue}</Badge>{/if}
				</span>
				{#if row.description}
					<span class="block max-w-xs truncate text-xs font-normal text-slate-500">{row.description}</span>
				{/if}
			{/snippet}
		</DataTable>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={tasks.page} total={tasks.total} unit="tugas" disabled={tasks.loading} onchange={(page) => tasks.setPage(page)} />
		</div>
	{/if}
</Card>
