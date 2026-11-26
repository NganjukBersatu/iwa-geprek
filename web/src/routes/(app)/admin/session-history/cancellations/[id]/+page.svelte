<script lang="ts">
	import { page } from '$app/state';
	import CancellationDetail from '$lib/features/cancellations/components/CancellationDetail.svelte';
</script>

<CancellationDetail id={page.params['id'] as string} />
