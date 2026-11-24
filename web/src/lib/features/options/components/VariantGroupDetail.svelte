<script lang="ts">
	import { dynamicStyle } from '$lib/motion/actions';
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { OptionMenu, VariantGroup, VariantGroupUpdate } from '$lib/api/types';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import { toast } from '$lib/components/feedback/toast.svelte';
	import { formatNumber } from '$lib/format/currency';
	import FigureGrid from '$lib/components/card/FigureGrid.svelte';
	import { scopeText } from '$lib/components/form/branch-prices.svelte';
	import { branches } from '$lib/stores/branch';
	import { PAGES, variantGroupPath } from '$lib/nav/pages';
	import { branchList } from '$lib/stores/branch';
	import { recordText } from '$lib/text/record-detail';
	import RecordDetailView from '../../record-detail/components/RecordDetailView.svelte';
	import { RecordDetailState } from '../../record-detail/record-detail.svelte';
	import { asLines, OptionRecipeEditor } from '../recipe-editor.svelte';
	import OptionRecipeDialog from './OptionRecipeDialog.svelte';
	import VariantGroupForm from './VariantGroupForm.svelte';
	import { termText } from '$lib/text/terms';
	import { optionText } from '$lib/text/options';
	import { format } from '$lib/text/format';

	type GroupContext = { menus: OptionMenu[]; outlets: { id: string; name: string }[] };

	let { id }: { id: string } = $props();

	const detail = new RecordDetailState<VariantGroup, VariantGroupUpdate, GroupContext>(untrack(() => id), {
		load: (groupId) => api.options.group(groupId),
		context: async () => {
			const [menus, outlets] = await Promise.all([api.options.menus(), branchList()]);
			return { menus, outlets };
		},
		update: (group, body) => api.options.updateGroup(group.id, body),
		remove: (group) => api.options.removeGroup(group.id),
		name: (group) => group.name,
		text: recordText('kelompok varian', PAGES.options.label)
	});

	const editor = new OptionRecipeEditor(async (text) => {
		toast.show(text);
		await detail.refresh();
	});

	const recipeText = (choice: VariantGroup['choices'][number]) =>
		choice.recipe.length > 0 ? choice.recipe.map((line) => `${line.ingredient_name} ${formatNumber(line.qty)} ${line.unit ?? ''}`.trim()).join(', ') : optionText.noExtraIngredientsTitle;
</script>

<RecordDetailView {detail} back={PAGES.options} trail={(group) => [{ label: PAGES.options.label, href: PAGES.options.path }, { label: group.name }]} tables={['variant_groups', 'variant_choices', 'variant_choice_recipes', 'menu_variant_groups']} title={(group) => group.name} description={() => optionText.groupDetailDescription}>
	{#snippet badge(group)}
		{#if group.required}<Badge tone="info">{optionText.required}</Badge>{/if}
		{#if !group.is_active}<Badge tone="neutral">{termText.inactive}</Badge>{/if}
	{/snippet}
	{#snippet body(group, context)}
		<Card flush>
			<div class="p-4 tablet:p-5">
				<FigureGrid
					label={optionText.groupSummary}
					figures={[
						{ label: termText.name, value: group.name },
						{ label: termText.branch, value: scopeText(group.outlet_id, $branches) },
						{ label: optionText.choices, value: group.required ? optionText.mustChoose : optionText.canSkip },
						{ label: termText.status, value: group.is_active ? termText.active : termText.inactive },
						{ label: optionText.choiceCount, value: formatNumber(group.choices.length, 0) }
					]}
				/>
			</div>
			<section class="flex flex-col gap-2 border-t border-slate-100 p-4 tablet:p-5">
				<h3 class="text-sm font-semibold text-slate-800">{optionText.choices}</h3>
				<ul class="flex flex-col divide-y divide-slate-100">
					{#each group.choices as choice (choice.id)}
						<li class="flex flex-wrap items-center gap-3 py-2 first:pt-0 last:pb-0">
							<span class="size-3.5 shrink-0 rounded-full border border-slate-200 bg-slate-300" use:dynamicStyle={{ 'background-color': choice.color }}></span>
							<span class="flex min-w-0 flex-1 flex-col">
								<span class="flex flex-wrap items-center gap-2 text-sm font-semibold text-slate-800">
									{choice.name}
									{#if !choice.is_active}<Badge tone="neutral">{termText.inactive}</Badge>{/if}
								</span>
								<span class="text-xs text-slate-500">{recipeText(choice)}</span>
							</span>
							<Button label={termText.recipe} icon="flask" variant="tertiary" small compact onclick={() => editor.open({ kind: 'varian', id: choice.id, title: `${group.name} · ${choice.name}`, lines: asLines(choice.recipe) })} />
						</li>
					{/each}
				</ul>
			</section>
			<section class="flex flex-col gap-2 border-t border-slate-100 p-4 tablet:p-5">
				<h3 class="text-sm font-semibold text-slate-800">{format(optionText.menusWithCount, { count: formatNumber(group.menu_ids.length, 0) })}</h3>
				{#if group.menu_ids.length === 0}
					<p class="text-xs text-slate-500">{optionText.notAttachedToMenus}</p>
				{:else}
					<ul class="flex flex-wrap gap-2">
						{#each group.menu_ids as menuId (menuId)}
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
		<VariantGroupForm group={props.record} menus={props.context?.menus ?? []} busy={props.busy} error={props.error} fieldErrors={props.fieldErrors} onsave={(body) => props.onsave(body as VariantGroupUpdate)} onclose={props.onclose} />
	{/snippet}
	{#snippet removeNote()}
		{optionText.groupRemoveNote}
	{/snippet}
</RecordDetailView>
