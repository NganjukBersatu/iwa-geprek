<script lang="ts">
	import { page } from '$app/state';
	import BranchDetailView from '$lib/features/branch-detail/components/BranchDetailView.svelte';
	import { BranchDetailState } from '$lib/features/branch-detail/branch-detail.svelte';

	const detail = new BranchDetailState(page.params['id'] as string);
</script>

<BranchDetailView {detail} />
