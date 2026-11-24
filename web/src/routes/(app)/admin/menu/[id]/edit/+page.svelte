<script lang="ts">
	import { page } from '$app/state';
	import MenuDetailView from '$lib/features/menu-detail/components/MenuDetailView.svelte';
	import { MenuDetailState } from '$lib/features/menu-detail/menu-detail.svelte';

	const menu = new MenuDetailState(page.params['id'] as string);
</script>

<MenuDetailView {menu} />
