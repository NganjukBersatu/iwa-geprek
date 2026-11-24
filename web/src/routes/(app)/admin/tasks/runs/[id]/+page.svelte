<script lang="ts">
	import { page } from '$app/state';
	import BatchRunDetail from '$lib/features/batches/components/BatchRunDetail.svelte';
</script>

{#key page.params['id']}
	<BatchRunDetail id={page.params['id'] as string} />
{/key}
