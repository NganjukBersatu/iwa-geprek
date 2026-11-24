<script lang="ts">
	import { page } from '$app/state';
	import BatchDetail from '$lib/features/batches/components/BatchDetail.svelte';
</script>

<BatchDetail id={page.params['id'] as string} />
