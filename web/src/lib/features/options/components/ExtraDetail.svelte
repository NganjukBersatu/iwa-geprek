<script lang="ts">
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { Extra, ExtraCategory, ExtraUpdate, OptionMenu } from '$lib/api/types';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import { toast } from '$lib/components/feedback/toast.svelte';
	import { sellersText } from '$lib/components/form/branch-prices.svelte';
	import { EMPTY_VALUE, formatNumber, formatRupiah } from '$lib/format/currency';
	import FigureGrid from '$lib/components/card/FigureGrid.svelte';
	import { PAGES } from '$lib/nav/pages';
	import { branchList } from '$lib/stores/branch';
	import { recordText } from '$lib/text/record-detail';
	import RecordDetailView from '../../record-detail/components/RecordDetailView.svelte';
	import { RecordDetailState } from '../../record-detail/record-detail.svelte';
	import { asLines, OptionRecipeEditor } from '../recipe-editor.svelte';
	import ExtraForm from './ExtraForm.svelte';
	import OptionRecipeDialog from './OptionRecipeDialog.svelte';
	import { termText } from '$lib/text/terms';
	import { optionText } from '$lib/text/options';
	import { format } from '$lib/text/format';

	type ExtraContext = { menus: OptionMenu[]; categories: ExtraCategory[]; outlets: { id: string; name: string }[] };

	let { id }: { id: string } = $props();


	const detail = new RecordDetailState<Extra, ExtraUpdate, ExtraContext>(untrack(() => id), {
		load: (extraId) => api.options.extra(extraId),
		context: async () => {
			const [menus, categories, outlets] = await Promise.all([api.options.menus(), api.options.categories(), branchList()]);
			return { menus, categories, outlets };
		},
		update: (extra, body) => api.options.updateExtra(extra.id, body),
		remove: (extra) => api.options.removeExtra(extra.id),
		name: (extra) => extra.name,
		text: recordText('ekstra', PAGES.options.label)
	});

	const editor = new OptionRecipeEditor(async (text) => {
		toast.show(text);
		await detail.refresh();
	});
</script>

<RecordDetailView {detail} back={PAGES.options} trail={(extra) => [{ label: PAGES.options.label, href: PAGES.options.path }, { label: extra.name }]} tables={['extras', 'extra_outlet_prices', 'extra_recipes', 'menu_extras']} title={(extra) => extra.name} description={() => optionText.extraDetailDescription}>
	{#snippet badge(extra)}
		{#if !extra.is_active}<Badge tone="neutral">{termText.inactive}</Badge>{/if}
	{/snippet}
	{#snippet extraActions(extra)}
		<Button label={termText.recipe} icon="flask" variant="tertiary" disabled={detail.busy} onclick={() => editor.open({ kind: 'ekstra', id: extra.id, title: extra.name, lines: asLines(extra.recipe) })} />
	{/snippet}
	{#snippet body(extra, context)}
		<Card flush>
			<div class="p-4 tablet:p-5">
				<FigureGrid
					label={optionText.extraSummary}
					figures={[
						{ label: termText.name, value: extra.name },
						{ label: termText.category, value: extra.category_name ?? EMPTY_VALUE },
						{ label: termText.basePrice, value: formatRupiah(extra.price) },
						{ label: optionText.availableIn, value: sellersText(extra, context?.outlets ?? []) }
					]}
				/>
			</div>
			<section class="flex flex-col gap-2 border-t border-slate-100 p-4 tablet:p-5">
				<h3 class="text-sm font-semibold text-slate-800">{optionText.pricePerBranch}</h3>
				{#if Object.keys(extra.branch_prices).length === 0}
					<p class="text-xs text-slate-500">{optionText.allBranchesBasePrice}</p>
				{:else}
					<ul class="flex flex-col divide-y divide-slate-100 text-xs">
						{#each Object.entries(extra.branch_prices) as [outletId, price] (outletId)}
							<li class="flex justify-between gap-3 py-1.5 first:pt-0 last:pb-0"><span class="text-slate-700">{context?.outlets.find((outlet) => outlet.id === outletId)?.name ?? outletId}</span><span class="font-semibold text-slate-800">{formatRupiah(price)}</span></li>
						{/each}
					</ul>
				{/if}
			</section>
			<section class="flex flex-col gap-2 border-t border-slate-100 p-4 tablet:p-5">
				<h3 class="text-sm font-semibold text-slate-800">{optionText.extraIngredients}</h3>
				{#if extra.recipe.length === 0}
					<p class="text-xs text-slate-500">{optionText.noExtraIngredients}</p>
				{:else}
					<ul class="flex flex-col divide-y divide-slate-100 text-xs">
						{#each extra.recipe as line (line.ingredient_id)}
							<li class="flex justify-between gap-3 py-1.5 first:pt-0 last:pb-0"><span class="text-slate-700">{line.ingredient_name}</span><span class="font-semibold text-slate-800">{`${formatNumber(line.qty)} ${line.unit ?? ''}`.trim()}</span></li>
						{/each}
					</ul>
				{/if}
			</section>
			<section class="flex flex-col gap-2 border-t border-slate-100 p-4 tablet:p-5">
				<h3 class="text-sm font-semibold text-slate-800">{format(optionText.menusWithCount, { count: formatNumber(extra.menu_ids.length, 0) })}</h3>
				{#if extra.menu_ids.length === 0}
					<p class="text-xs text-slate-500">{optionText.notAttachedToMenus}</p>
				{:else}
					<ul class="flex flex-wrap gap-2">
						{#each extra.menu_ids as menuId (menuId)}
							<li><Badge tone="brand">{context?.menus.find((menu) => menu.id === menuId)?.name ?? menuId}</Badge></li>
						{/each}
					</ul>
				{/if}
			</section>
		</Card>
		{#if editor.recipe}
			{#key editor.round}
				<OptionRecipeDialog
					target={editor.recipe}
					bind:outletId={editor.branch}
					onbranch={(outletId) => void editor.loadFor(outletId)}
					canSpread={(context?.outlets.length ?? 0) > 1}
					busy={editor.busy}
					error={editor.error}
					onsave={(body) => void editor.save(body)}
					onclose={() => editor.close()}
				/>
			{/key}
		{/if}
	{/snippet}
	{#snippet form(props)}
		<ExtraForm extra={props.record} menus={props.context?.menus ?? []} categories={props.context?.categories ?? []} outlets={props.context?.outlets ?? []} busy={props.busy} error={props.error} fieldErrors={props.fieldErrors} onsave={(body) => props.onsave(body as ExtraUpdate)} onclose={props.onclose} />
	{/snippet}
	{#snippet removeNote()}
		{optionText.extraRemoveNote}
	{/snippet}
</RecordDetailView>
