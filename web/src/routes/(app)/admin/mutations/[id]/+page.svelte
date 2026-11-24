<script lang="ts">
	import { page } from '$app/state';
	import MutationDetail from '$lib/features/mutations/components/MutationDetail.svelte';
</script>

<MutationDetail id={page.params['id'] as string} />
