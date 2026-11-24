<script lang="ts">
	import { page } from '$app/state';
	import TargetDetailView from '$lib/features/stations/components/TargetDetailView.svelte';
	import { TargetDetailState } from '$lib/features/stations/target-detail.svelte';

	const target = new TargetDetailState(page.params['id'] as string);
</script>

<TargetDetailView {target} />
