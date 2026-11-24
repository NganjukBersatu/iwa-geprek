<script lang="ts">
	import { page } from '$app/state';
	import PromoDetail from '$lib/features/promotions/components/PromoDetail.svelte';
</script>

<PromoDetail id={page.params['id'] as string} />
