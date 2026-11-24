<script lang="ts">
	import { page } from '$app/state';
	import AnnouncementDetail from '$lib/features/promotions/components/AnnouncementDetail.svelte';
</script>

<AnnouncementDetail id={page.params['id'] as string} />
