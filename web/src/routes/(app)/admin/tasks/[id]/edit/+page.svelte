<script lang="ts">
	import { page } from '$app/state';
	import TaskDetail from '$lib/features/tasks/components/TaskDetail.svelte';
</script>

<TaskDetail id={page.params['id'] as string} />
