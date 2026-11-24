<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import type { MenuCategory, MenuCreate } from '$lib/api/types';
	import { userMessage } from '$lib/api/user-message';
	import Banner from '$lib/components/card/Banner.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import BulkEntryDialog from '$lib/components/dialog/BulkEntryDialog.svelte';
	import type { Field } from '$lib/components/form/types';
	import { PAGES } from '$lib/nav/pages';
	import MenuCategoryMissing from '../../menu-categories/components/MenuCategoryMissing.svelte';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { menuText } from '$lib/text/menu';

	let categories = $state<MenuCategory[] | null>(null);
	let error = $state('');

	async function load(): Promise<void> {
		error = '';
		try {
			categories = await api.menu.categories();
		} catch (cause) {
			error = userMessage(cause, menuText.categoriesLoadFailed);
		}
	}

	onMount(() => void load());

	const entryColumns = $derived<Field[]>([
		{ key: 'name', label: menuText.menuName, required: true },
		{ key: 'price', label: termText.basePrice, kind: 'number', required: true },
		{ key: 'category_id', label: termText.category, kind: 'select', required: true, options: (categories ?? []).map((category) => ({ value: category.id, label: category.name })) },
		{ key: 'description', label: termText.description }
	]);

	function menuOf(row: Record<string, string | number>): MenuCreate {
		return {
			name: String(row['name']),
			price: String(row['price']),
			category_id: String(row['category_id']),
			description: row['description'] ? String(row['description']) : null,
			is_available: true
		};
	}
</script>

{#if error}
	<Banner tone="danger" icon="alert-triangle" title={actionText.pageLoadFailed}>
		{error}
		{#snippet action()}
			<Button label={actionText.retry} onclick={() => void load()} />
		{/snippet}
	</Banner>
{:else if categories && categories.length === 0}
	<MenuCategoryMissing />
{:else if categories}
	<BulkEntryDialog
		asPage
		title={menuText.bulkTitle}
		hint={menuText.bulkHint}
		columns={entryColumns}
		submit={(rows) => api.menu.bulk.create(rows.map(menuOf))}
		submitLabel="Simpan semua menu"
		onclose={() => void goto(PAGES.menu.path)}
	/>
{:else}
	<Notice loading text={menuText.categoriesLoading} />
{/if}
