<script lang="ts">
	import MonitorView from '$lib/features/stations/components/MonitorView.svelte';
	import { MonitorState } from '$lib/features/stations/monitor.svelte';

	const monitor = new MonitorState();
</script>

<MonitorView {monitor} />
