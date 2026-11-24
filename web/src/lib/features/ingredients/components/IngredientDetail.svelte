<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { CatalogEntry, Ingredient, IngredientImpact, IngredientOptions, IngredientUpdate } from '$lib/api/types';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import FigureCards from '$lib/components/card/FigureCards.svelte';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import { EMPTY_VALUE, formatNumber, formatRupiah } from '$lib/format/currency';
	import { PAGES } from '$lib/nav/pages';
	import { STOCK_TABLES } from '$lib/live/tables';
	import { branchList } from '$lib/stores/branch';
	import { recordText } from '$lib/text/record-detail';
	import RecordDetailView from '../../record-detail/components/RecordDetailView.svelte';
	import { RecordDetailState } from '../../record-detail/record-detail.svelte';
	import { stockBadge } from '../stock-level';
	import IngredientForm from './IngredientForm.svelte';
	import LinkDialog from './LinkDialog.svelte';
	import { termText } from '$lib/text/terms';
	import { ingredientText } from '$lib/text/ingredients';
	import { format } from '$lib/text/format';
	import RichText from '$lib/components/text/RichText.svelte';

	type IngredientContext = { options: IngredientOptions; outlets: { id: string; name: string }[] };
	type IngredientSave = { body: IngredientUpdate; photo: File | null };

	let { id }: { id: string } = $props();

	const detail = new RecordDetailState<Ingredient, IngredientSave, IngredientContext>(untrack(() => id), {
		load: (ingredientId) => api.ingredients.detail(ingredientId),
		context: async () => {
			const [options, outlets] = await Promise.all([api.ingredients.options(), branchList()]);
			return { options, outlets };
		},
		update: async (ingredient, { body, photo }) => {
			const saved = await api.ingredients.update(ingredient.id, body);
			return photo ? api.ingredients.uploadPhoto(saved.id, photo) : saved;
		},
		remove: (ingredient) => api.ingredients.remove(ingredient.id),
		name: (ingredient) => ingredient.name,
		text: recordText('bahan', PAGES.ingredients.label)
	});

	let catalog = $state<CatalogEntry[]>([]);
	let linking = $state(false);
	let impact = $state<IngredientImpact | null>(null);

	const branchName = (ingredient: Ingredient, context: IngredientContext | null) => context?.outlets.find((outlet) => outlet.id === ingredient.outlet_id)?.name ?? EMPTY_VALUE;
	const impactLines = $derived(
		impact
			? ([[impact.recipes, 'baris resep'], [impact.movements, 'catatan mutasi stok']] as [number, string][]).filter(([count]) => count > 0)
			: []
	);

	// The count of what goes with the ingredient is read when the delete question opens.
	$effect(() => {
		if (!detail.removing) {
			impact = null;
			return;
		}
		const ingredient = untrack(() => detail.record);
		if (ingredient && impact === null) void api.ingredients.impact(ingredient.id).then((found) => (impact = found)).catch(() => undefined);
	});

	async function openLink(): Promise<void> {
		const done = await detail.run(async () => {
			catalog = await api.ingredients.catalog();
		}, ingredientText.catalogLoadFailed);
		if (done) linking = true;
	}

	async function link(catalogId: string | null): Promise<void> {
		const done = await detail.change(
			(current) => api.ingredients.link(current.id, catalogId ? { catalog_id: catalogId, create_new: false } : { create_new: true }),
			ingredientText.linkFailed
		);
		if (done) linking = false;
	}
</script>

<RecordDetailView
	{detail}
	back={PAGES.ingredients}
	trail={(ingredient) => [{ label: PAGES.ingredients.label, href: PAGES.ingredients.path }, ...(ingredient.category ? [{ label: ingredient.category }] : []), { label: ingredient.name }]}
	tables={STOCK_TABLES}
	title={(ingredient) => ingredient.name}
	description={(ingredient, context) => `${ingredient.category ? `${ingredient.category} · ` : ''}${branchName(ingredient, context)}`}
>
	{#snippet badge(ingredient)}
		<Badge tone={ingredient.is_active ? 'success' : 'neutral'}>{ingredient.is_active ? termText.active : termText.inactive}</Badge>
		{#if ingredient.stock_level}
			{@const stock = stockBadge(ingredient.stock_level)}
			<Badge tone={stock.tone} title={ingredient.stock_level === 'negative' ? ingredientText.negativeStockHint : undefined}>{stock.label}</Badge>
		{/if}
	{/snippet}
	{#snippet extraActions(ingredient)}
		{#if !ingredient.catalog_id}
			<Button label={ingredientText.link} icon="link" variant="tertiary" disabled={detail.busy} onclick={() => void openLink()} />
		{/if}
	{/snippet}
	{#snippet body(ingredient, context)}
		<FigureCards
			label={ingredientText.summary}
			figures={[
				{ label: ingredientText.stockBalance, value: `${formatNumber(ingredient.balance)} ${ingredient.unit}` },
				{ label: ingredientText.minimumLimit, value: `${formatNumber(ingredient.minimum)} ${ingredient.unit}` },
				{ label: ingredientText.unitPrice, value: formatRupiah(ingredient.unit_price) },
				{ label: ingredientText.usedIn, value: ingredient.catalog_id ? format(ingredientText.branchCount, { count: formatNumber(ingredient.branch_count, 0) }) : branchName(ingredient, context) }
			]}
		/>
		<div class="grid items-start gap-4 tablet:gap-6 laptop:grid-cols-[20rem_minmax(0,1fr)]">
			<Card flush>
				<div class="flex flex-col gap-3 bg-brand-soft p-4">
					<span class="text-xs font-medium text-brand-deep">{ingredientText.photo}</span>
					<div class="flex aspect-4/3 items-center justify-center overflow-hidden rounded-lg bg-brand-tint">
						{#if ingredient.photo_url}
							<img src={ingredient.photo_url} alt={format(controlText.photoOf, { name: ingredient.name })} class="size-full object-cover" />
						{:else}
							<span class="flex flex-col items-center gap-2 text-xs text-brand-deep">
								<i class="ti ti-photo text-display" aria-hidden="true"></i>
								{ingredientText.noPhoto}
							</span>
						{/if}
					</div>
				</div>
				<div class="flex flex-col gap-3 border-t border-brand-line p-4">
					<FigureList
						title={ingredientText.information}
						figures={[
							{ label: termText.branch, value: branchName(ingredient, context) },
							{ label: termText.category, value: ingredient.category ?? EMPTY_VALUE },
							{ label: termText.unit, value: ingredient.unit },
							{ label: ingredientText.available, value: ingredient.is_available ? termText.yes : termText.no },
							{ label: ingredientText.catalog, value: ingredient.catalog_id ? format(ingredientText.linkedBranches, { count: formatNumber(ingredient.branch_count, 0) }) : ingredientText.notLinked }
						]}
					/>
				</div>
			</Card>
			<div class="flex min-w-0 flex-col gap-4 tablet:gap-6">
				<Card>
					<FigureList
						title={termText.stock}
						figures={[
							{ label: ingredientText.stockBalance, value: `${formatNumber(ingredient.balance)} ${ingredient.unit}` },
							{ label: ingredientText.minimumLimit, value: `${formatNumber(ingredient.minimum)} ${ingredient.unit}` },
							{ label: ingredientText.lastMove, value: ingredient.days_since_move === null ? EMPTY_VALUE : format(ingredientText.daysAgo, { days: formatNumber(ingredient.days_since_move, 0) }) },
							{ label: ingredientText.dormant, value: ingredient.is_dormant ? termText.yes : termText.no }
						]}
					/>
				</Card>
				<Card>
					<FigureList
						title={termText.price}
						figures={[
							{ label: ingredientText.packagePrice, value: formatRupiah(ingredient.package_price) },
							{ label: ingredientText.packageSize, value: `${formatNumber(ingredient.package_size)} ${ingredient.unit}` },
							{ label: ingredientText.unitPrice, value: formatRupiah(ingredient.unit_price) },
							{ label: ingredientText.shrinkTolerance, value: `${formatNumber(ingredient.shrink_tolerance)}%` }
						]}
					/>
				</Card>
			</div>
		</div>
	{/snippet}
	{#snippet form(props)}
		<IngredientForm
			ingredient={props.record}
			options={props.context?.options ?? { categories: [], units: [] }}
			busy={props.busy}
			error={props.error}
			fieldErrors={props.fieldErrors}
			onsave={(body, photo) => props.onsave({ body: body as IngredientUpdate, photo })}
			onremovephoto={async () => {
				if (await detail.change((current) => api.ingredients.removePhoto(current.id), ingredientText.removePhotoFailed)) detail.closeDialogs();
			}}
			onclose={props.onclose}
		/>
	{/snippet}
	{#snippet removeNote(ingredient)}
		<p><RichText template={ingredientText.ingredientRemoveNote} values={{ name: ingredient.name }} /></p>
		{#if impact === null}
			<p class="mt-2 text-slate-600">{ingredientText.countingRemoved}</p>
		{:else if impactLines.length > 0}
			<p class="mt-2">{ingredientText.removedData}</p>
			<ul class="mt-1 list-disc pl-5">
				{#each impactLines as [count, label] (label)}
					<li><strong class="text-slate-800">{formatNumber(count, 0)}</strong> {label}</li>
				{/each}
			</ul>
			<p class="mt-2">{ingredientText.removeRecipeNote}</p>
		{/if}
	{/snippet}
</RecordDetailView>

{#if linking && detail.record}
	<LinkDialog ingredient={detail.record} {catalog} busy={detail.busy} error={detail.actionError} onconfirm={(catalogId) => void link(catalogId)} onclose={() => (linking = false)} />
{/if}
