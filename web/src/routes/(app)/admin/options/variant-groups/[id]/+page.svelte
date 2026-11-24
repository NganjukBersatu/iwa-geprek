<script lang="ts">
	import { page } from '$app/state';
	import VariantGroupDetail from '$lib/features/options/components/VariantGroupDetail.svelte';
</script>

<VariantGroupDetail id={page.params['id'] as string} />
