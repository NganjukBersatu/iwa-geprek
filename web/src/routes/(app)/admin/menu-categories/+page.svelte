<script lang="ts">
	import Button from '$lib/components/button/Button.svelte';
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import MenuCategoriesView from '$lib/features/menu-categories/components/MenuCategoriesView.svelte';
	import { MenuCategoriesState } from '$lib/features/menu-categories/menu-categories.svelte';
	import { pageText } from '$lib/text/pages';

	const categories = new MenuCategoriesState();
</script>

<ManageShell manage={categories} title={pageText.menuCategoriesTitle} description={pageText.menuCategoriesDescription} loadingText={pageText.loadingMenuCategories}>
	{#snippet actions()}
		<Button label={pageText.addCategory} icon="plus" variant="primary" compact onclick={() => categories.openNew()} />
	{/snippet}
	{#snippet children()}
		<MenuCategoriesView {categories} />
	{/snippet}
</ManageShell>
