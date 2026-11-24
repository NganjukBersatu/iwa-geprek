<script lang="ts">
	import { page } from '$app/state';
	import TaskCreate from '$lib/features/tasks/components/TaskCreate.svelte';
	import { TASK_SOURCE_PARAM } from '$lib/nav/pages';

	const sourceRunId = $derived(page.url.searchParams.get(TASK_SOURCE_PARAM));
</script>

{#key sourceRunId}
	<TaskCreate {sourceRunId} />
{/key}
