<script lang="ts">
	import { page } from '$app/state';
	import LossDetail from '$lib/features/ingredient-losses/components/LossDetail.svelte';
</script>

<LossDetail id={page.params['id'] as string} />
