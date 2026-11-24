<script lang="ts">
	import SetupView from '$lib/features/stations/components/SetupView.svelte';
	import { SetupState } from '$lib/features/stations/setup.svelte';

	const setup = new SetupState();
</script>

<SetupView {setup} />
