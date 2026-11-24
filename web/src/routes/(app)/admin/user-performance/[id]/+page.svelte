<script lang="ts">
	import { page } from '$app/state';
	import UserPerformanceDetailView from '$lib/features/user-performance/components/UserPerformanceDetailView.svelte';
	import { UserPerformanceDetailState } from '$lib/features/user-performance/user-performance-detail.svelte';

	const detail = new UserPerformanceDetailState(page.params['id'] as string);
</script>

<UserPerformanceDetailView {detail} />
