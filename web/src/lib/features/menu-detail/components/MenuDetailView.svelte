<script lang="ts">
	import { menuText } from '$lib/text/menu';
	import { termText } from '$lib/text/terms';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import PageIntro from '$lib/components/header/PageIntro.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import { sellersText } from '$lib/components/form/branch-prices.svelte';
	import { live } from '$lib/live/live';
	import { MENU_TABLES } from '$lib/live/tables';
	import { PAGES } from '$lib/nav/pages';
	import type { MenuCreate, MenuUpdate } from '$lib/api/types';
	import MenuForm from '../../menu/components/MenuForm.svelte';
	import { editAddress } from '../../record-detail/edit-address.svelte';
	import type { MenuDetailState } from '../menu-detail.svelte';
	import MenuBranchPrices from './MenuBranchPrices.svelte';
	import MenuFixedCost from './MenuFixedCost.svelte';
	import MenuManage from './MenuManage.svelte';
	import MenuProfile from './MenuProfile.svelte';
	import MenuRecipes from './MenuRecipes.svelte';
	import MenuSummary from './MenuSummary.svelte';
	import { actionText } from '$lib/text/actions';
	import { menuDetailText } from '$lib/text/menu-detail';

	let { menu }: { menu: MenuDetailState } = $props();

	const item = $derived(menu.item);
	const sellers = $derived(item ? sellersText(item, menu.outlets) : '');

	const address = editAddress();

	async function saveAndReturn(body: MenuCreate | MenuUpdate, photo: File | null): Promise<void> {
		if (await menu.save(body, photo)) void goto(address.recordPath);
	}

	onMount(() => {
		void menu.load();
		return live.on(MENU_TABLES, () => void menu.refresh());
	});
</script>

{#if menu.error}
	<Banner tone="danger" icon="alert-triangle" title={menuDetailText.loadFailedTitle}>
		{menu.error}
		{#snippet action()}
			<Button label={actionText.retry} onclick={() => void menu.load()} />
		{/snippet}
	</Banner>
{:else if item && address.editing}
	<MenuForm {item} categories={menu.categories} outlets={menu.outlets} busy={menu.busy} error={menu.actionError} fieldErrors={menu.fieldErrors} onsave={(body, photo) => void saveAndReturn(body, photo)} onclose={() => void goto(address.recordPath)} />
{:else if item}
	<div class="flex flex-col gap-4 tablet:gap-6">
		<PageIntro
			title={item.name}
			description="{item.category_name ? `${item.category_name} · ` : ''}{sellers}"
			items={[{ label: PAGES.menu.label, href: PAGES.menu.path }, ...(item.category_name ? [{ label: item.category_name }] : []), { label: item.name }]}
		>
			{#snippet badge()}
				<Badge tone={item.is_available ? 'success' : 'danger'}>{item.is_available ? menuText.available : termText.outOfStock}</Badge>
			{/snippet}
			{#snippet actions()}
				<MenuManage {menu} {item} ondeleted={() => void goto(PAGES.menu.path)} />
			{/snippet}
		</PageIntro>

		{#if menu.actionError && !menu.removing && !menu.fixedCostEditing && !menu.fixedCostClearing}
			<Banner tone="danger" icon="alert-triangle">{menu.actionError}</Banner>
		{/if}

		<MenuSummary {item} {sellers} />
		<MenuProfile {item} />
		<MenuBranchPrices {item} outlets={menu.outlets} />
		{#if menu.seesFixedCost}
			<MenuFixedCost {menu} {item} />
		{/if}
		{#if menu.recipes.canRead && !item.has_fixed_cost}
			<MenuRecipes {menu} />
		{/if}
	</div>
{:else}
	<Notice loading text={menuDetailText.loading} />
{/if}
