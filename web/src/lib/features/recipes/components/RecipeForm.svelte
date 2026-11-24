<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import { PAGES, recipePath } from '$lib/nav/pages';
	import { recipeKey } from '../recipe-key';
	import { api } from '$lib/api';
	import { RECIPE_CHOICE_SIZE } from '$lib/api/recipes';
	import type { IngredientOption, Recipe, RecipeSave } from '$lib/api/types';
	import { byPage, RemoteChoices } from '$lib/components/form/remote-choices.svelte';
	import { parseNumber } from '$lib/format/number';
	import { SvelteMap } from 'svelte/reactivity';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import DeleteButton from '$lib/components/button/DeleteButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import FormSection from '$lib/components/form/FormSection.svelte';
	import CheckRow from '$lib/components/form/CheckRow.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import { formatRupiah } from '$lib/format/currency';
	import { untrack } from 'svelte';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { recipeText } from '$lib/text/recipes';
	import { format } from '$lib/text/format';

	let {
		recipe,
		seesCost,
		canSpread,
		busy,
		error,
		fieldErrors = {},
		onsave,
		onclose
	}: {
		recipe: Recipe;
		seesCost: boolean;
		canSpread: boolean;
		busy: boolean;
		error: string;
		/** What the server refused, by field name, shown under the field itself. */
		fieldErrors?: Record<string, string>;
		onsave: (body: RecipeSave) => void;
		onclose: () => void;
	} = $props();

	const FOLLOW = '';
	const current = untrack(() => recipe);
	const trail = [
		{ label: PAGES.recipes.label, href: PAGES.recipes.path },
		{ label: current.menu_name, href: recipePath(recipeKey.join(current.menu_id, current.outlet_id)) },
		{ label: actionText.edit }
	];
	const asText = (value: unknown) => (value === null || value === undefined ? '' : String(Number(value)));

	let lines = $state(current.lines.map((line) => ({ ingredient_id: line.ingredient_id, qty: asText(line.qty) })));
	let addKind = $state<string>(current.add_cost_custom ? (current.add_cost_kind ?? FOLLOW) : FOLLOW);
	let addValue = $state(current.add_cost_custom ? asText(current.add_cost_value) : '');
	let overhead = $state(asText(current.overhead === null || Number(current.overhead) === 0 ? null : current.overhead));
	let target = $state(current.target_custom ? asText(current.target_margin_percent) : '');
	let everyBranch = $state(false);

	/** The first line answers to the field's own name, which is what the server names; the lines after it get a number. */
	const lineField = (field: string, index: number) => (index === 0 ? field : `${field}_${index}`);
	const errors = new FieldErrors(
		() => ({
			...Object.fromEntries(lines.flatMap((_, index) => [[lineField('ingredient_id', index), format(recipeText.ingredientNumber, { number: index + 1 })], [lineField('qty', index), format(recipeText.ingredientQuantityNumber, { number: index + 1 })]])),
			add_cost_kind: recipeText.addCost,
			add_cost_value: recipeText.addCostValue,
			overhead: recipeText.overhead,
			target_margin_percent: recipeText.marginTarget
		}),
		() => fieldErrors
	);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(fieldErrors).length > 0) void focusRefused();
	});

	// Dicari dan dimuat per halaman di server, supaya cabang dengan ribuan bahan tidak memuat semuanya sekaligus.
	const ingredients = new RemoteChoices<IngredientOption>(
		byPage(RECIPE_CHOICE_SIZE, (query, page) => api.recipes.ingredients(current.outlet_id, query, page)),
		(item) => item.id
	);
	ingredients.search('');
	// Bahan yang sudah ada di resep atau sudah dipilih diingat beserta harganya, supaya nama dan biaya tetap ada walau tidak ada di hasil cari terakhir.
	const known = new SvelteMap<string, IngredientOption>(
		current.lines.map((line) => [line.ingredient_id, { id: line.ingredient_id, name: line.ingredient_name, unit: line.unit, unit_price: line.unit_price }] as const)
	);
	const label = (item: IngredientOption) => (item.unit ? `${item.name} (${item.unit})` : item.name);
	function optionsFor(id: string): { value: string; label: string }[] {
		const chosen = known.get(id);
		const list = chosen && !ingredients.items.some((item) => item.id === id) ? [chosen, ...ingredients.items] : ingredients.items;
		return list.map((item) => ({ value: item.id, label: label(item) }));
	}
	function pick(line: { ingredient_id: string }, id: string): void {
		const choice = ingredients.items.find((item) => item.id === id) ?? known.get(id);
		if (choice) known.set(choice.id, choice);
		line.ingredient_id = id;
	}
	const priceOf = (id: string) => known.get(id)?.unit_price ?? null;
	const noIngredients = $derived(!ingredients.searching && ingredients.typed === '' && ingredients.items.length === 0 && ingredients.problem === '');
	const decimal = (text: string) => parseNumber(text) ?? Number.NaN;
	const ingredientsCost = $derived(lines.reduce((total, line) => total + (parseNumber(line.qty) ?? 0) * Number(priceOf(line.ingredient_id) ?? 0), 0));

	const addLine = () => (lines = [...lines, { ingredient_id: '', qty: '' }]);
	const removeLine = (index: number) => (lines = lines.filter((_, position) => position !== index));

	let emptyProblem = $state('');

	function submit(): void {
		emptyProblem = '';
		const found: Record<string, string> = {};
		const seen = new Set<string>();
		lines.forEach((line, index) => {
			if (!line.ingredient_id) return;
			if (!(decimal(line.qty) > 0)) found[lineField('qty', index)] = recipeText.quantityInvalid;
			if (seen.has(line.ingredient_id)) found[lineField('ingredient_id', index)] = recipeText.duplicateIngredient;
			seen.add(line.ingredient_id);
		});
		if (!errors.check(found)) return;
		const chosen = lines.filter((line) => line.ingredient_id);
		if (chosen.length === 0 && current.lines.length === 0) {
			emptyProblem = recipeText.noIngredientsChosen;
			return;
		}
		const body: RecipeSave = { lines: chosen.map((line) => ({ ingredient_id: line.ingredient_id, qty: String(decimal(line.qty)) })), all_branches: everyBranch };
		if (seesCost) {
			body.add_cost_kind = addKind === FOLLOW ? null : (addKind as 'persen' | 'rupiah');
			body.add_cost_value = addKind === FOLLOW ? null : String(decimal(addValue || '0'));
			body.overhead = overhead.trim() === '' ? null : String(decimal(overhead));
			body.target_margin_percent = target.trim() === '' ? null : String(decimal(target));
		}
		onsave(body);
	}
</script>

<FormPage title={format(recipeText.recipeOf, { name: current.menu_name })} description={recipeText.formDescription} stacked {trail} {busy} {onclose}>
	<FormSection icon="flask" title={termText.ingredient} description={recipeText.formDescription}>
		{#each lines as line, index (index)}
			<div class="grid items-end gap-2 tablet:grid-cols-[1fr_8rem_auto]">
				<SelectField
					label={format(recipeText.ingredientNumber, { number: index + 1 })}
					value={line.ingredient_id}
					options={optionsFor(line.ingredient_id)}
					empty={recipeText.chooseIngredient}
					hint={ingredients.problem || undefined}
					error={errors.get(lineField('ingredient_id', index))}
					onchange={(id) => pick(line, id)}
					onsearch={(text) => ingredients.search(text)}
					onmore={() => ingredients.more()}
					searching={ingredients.searching}
					loadingMore={ingredients.loadingMore}
				/>
				<TextField label={recipeText.quantity} inputmode="decimal" bind:value={line.qty} error={errors.get(lineField('qty', index))} />
				<DeleteButton small onclick={() => removeLine(index)} />
			</div>
		{/each}
		<Button label={controlText.addIngredient} icon="plus" variant="tertiary" small compact disabled={noIngredients} onclick={addLine} class="w-fit" />
		{#if noIngredients}
			<p class="text-xs text-slate-500">{recipeText.noActiveIngredients}</p>
		{/if}
	</FormSection>
	{#if seesCost}
		<FormSection icon="calculator" title={recipeText.recipeCost} description={format(recipeText.recipeTotalNote, { amount: formatRupiah(ingredientsCost) })}>
			<div class="grid gap-3 tablet:grid-cols-2">
				<SelectField
					label={recipeText.addCost}
					bind:value={addKind}
					options={[
						{ value: FOLLOW, label: recipeText.markupFollowSetting },
						{ value: 'persen', label: recipeText.markupPercent },
						{ value: 'rupiah', label: recipeText.markupRupiah }
					]}
					error={errors.get('add_cost_kind')}
				/>
				{#if addKind !== FOLLOW}
					<TextField label={addKind === 'persen' ? recipeText.addCostPercent : recipeText.addCostRupiah} inputmode="decimal" bind:value={addValue} error={errors.get('add_cost_value')} />
				{/if}
				<TextField label={recipeText.overheadRupiah} inputmode="decimal" bind:value={overhead} error={errors.get('overhead')} />
				<TextField label={recipeText.marginTargetPercent} inputmode="decimal" bind:value={target} hint={recipeText.suggestedPriceBasis} error={errors.get('target_margin_percent')} />
			</div>
		</FormSection>
	{/if}
	{#if canSpread}
		<FormSection icon="building-store" title={termText.branch} description={recipeText.copyDescription}>
			<CheckRow label={recipeText.applyToAllBranches} hint={recipeText.applyToAllBranchesHint} checked={everyBranch} onchange={() => (everyBranch = !everyBranch)} />
		</FormSection>
	{/if}
	{#if error && errors.count === 0}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
	{/if}
	{#if emptyProblem}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{emptyProblem}</Banner></div>
	{/if}

	{#snippet footer()}
		<SaveButton busy={busy} onclick={submit} />
		<CancelButton disabled={busy} onclick={onclose} />
	{/snippet}
</FormPage>
