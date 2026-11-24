<script lang="ts">
	import { page } from '$app/state';
	import BatchCreate from '$lib/features/batches/components/BatchCreate.svelte';
	import { BATCH_KIND_PARAM } from '$lib/nav/pages';

	const kind = $derived(page.url.searchParams.get(BATCH_KIND_PARAM) === 'routine' ? 'routine' : 'outlet');
</script>

{#key kind}
	<BatchCreate {kind} />
{/key}
