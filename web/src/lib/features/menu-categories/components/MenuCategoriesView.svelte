<script lang="ts">
	import { emptyText } from '$lib/text/empty';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { menuCategoryColumns } from '../columns';
	import type { MenuCategoriesState } from '../menu-categories.svelte';
	import MenuCategoryDialog from './MenuCategoryDialog.svelte';
	import { menuCategoryText } from '$lib/text/menu-categories';
	import RichText from '$lib/components/text/RichText.svelte';

	let { categories }: { categories: MenuCategoriesState } = $props();
</script>

{#if categories.actionError && !categories.formOpen && !categories.removing}
	<Banner tone="danger" icon="alert-triangle">{categories.actionError}</Banner>
{/if}

<Card flush>
	<CardHeader divided title={menuCategoryText.title} description={menuCategoryText.description} />
	{#if categories.items.length === 0}
		<Notice title={emptyText.menuCategories.title} text={emptyText.menuCategories.text}/>
	{:else}
		<DataTable sort={categories.sort} columns={menuCategoryColumns} rows={categories.items} rowKey={(row) => row.id} loading={categories.loading} onopen={(row) => categories.openEdit(row)} />
	{/if}
</Card>

{#if categories.formOpen}
	{#key categories.editing?.id ?? 'new'}
		<MenuCategoryDialog
			category={categories.editing}
			busy={categories.busy}
			error={categories.actionError}
			fieldErrors={categories.fieldErrors}
			onsave={(name) => void categories.save(name)}
			onremove={(category) => categories.askRemove(category)}
			onclose={() => categories.closeDialogs()}
		/>
	{/key}
{/if}

<ConfirmDialog
	open={categories.removing !== null}
	title={menuCategoryText.removeTitle}
	confirmLabel="Ya, hapus kategori"
	danger
	busy={categories.busy}
	error={categories.actionError}
	onconfirm={() => void categories.remove()}
	oncancel={() => categories.closeDialogs()}
>
	<RichText template={menuCategoryText.categoryRemoveNote} values={{ name: categories.removing?.name ?? '' }} />
</ConfirmDialog>
