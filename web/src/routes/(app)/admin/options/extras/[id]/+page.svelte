<script lang="ts">
	import { page } from '$app/state';
	import ExtraDetail from '$lib/features/options/components/ExtraDetail.svelte';
</script>

<ExtraDetail id={page.params['id'] as string} />
