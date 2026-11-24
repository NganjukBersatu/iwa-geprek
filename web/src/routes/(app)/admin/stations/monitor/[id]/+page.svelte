<script lang="ts">
	import { page } from '$app/state';
	import TaskView from '$lib/features/stations/components/TaskView.svelte';
	import { TaskState } from '$lib/features/stations/task.svelte';

	const task = new TaskState(page.params['id'] as string);
</script>

<TaskView {task} />
