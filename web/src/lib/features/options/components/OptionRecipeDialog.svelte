<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import { api } from '$lib/api';
	import type { IngredientOption, OptionRecipeSave } from '$lib/api/types';
	import { RECIPE_CHOICE_SIZE } from '$lib/api/recipes';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import DeleteButton from '$lib/components/button/DeleteButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Modal from '$lib/components/dialog/Modal.svelte';
	import BranchField from '$lib/components/form/BranchField.svelte';
	import CheckRow from '$lib/components/form/CheckRow.svelte';
	import { byPage, RemoteChoices } from '$lib/components/form/remote-choices.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { parseNumber } from '$lib/format/number';
	import { SvelteMap } from 'svelte/reactivity';
	import { untrack } from 'svelte';
	import type { RecipeTarget } from '../recipe-editor.svelte';
	import { optionText } from '$lib/text/options';
	import { format } from '$lib/text/format';

	let {
		target,
		outletId = $bindable(''),
		onbranch,
		canSpread,
		busy,
		error,
		onsave,
		onclose
	}: {
		target: RecipeTarget;
		outletId?: string;
		onbranch: (outletId: string) => void;
		canSpread: boolean;
		busy: boolean;
		error: string;
		onsave: (body: OptionRecipeSave) => void;
		onclose: () => void;
	} = $props();

	let lines = $state(untrack(() => target.lines.map((line) => ({ ingredient_id: line.ingredient_id, qty: line.qty }))));
	let everyBranch = $state(false);
	let problem = $state('');

	// Dicari dan dimuat per halaman di server untuk cabang yang dipilih, supaya ribuan bahan tidak dimuat sekaligus.
	const ingredients = new RemoteChoices<IngredientOption>(
		byPage(RECIPE_CHOICE_SIZE, (query, page) => (outletId ? api.options.ingredients(outletId, query, page) : Promise.resolve([]))),
		(item) => item.id
	);
	ingredients.search('');
	// Bahan yang sudah ada di resep atau sudah dipilih diingat, supaya namanya tetap ada walau tidak ada di hasil cari terakhir.
	const known = new SvelteMap<string, IngredientOption>(
		untrack(() => target.lines.map((line) => [line.ingredient_id, { id: line.ingredient_id, name: line.ingredient_name, unit: line.unit, unit_price: null }] as const))
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
	const noIngredients = $derived(!ingredients.searching && ingredients.typed === '' && ingredients.items.length === 0 && ingredients.problem === '');
	const decimal = (text: string) => parseNumber(text) ?? Number.NaN;

	function submit(): void {
		problem = '';
		if (!outletId) return void (problem = optionText.recipeBranchRequired);
		const chosen = lines.filter((line) => line.ingredient_id);
		if (chosen.some((line) => !(decimal(line.qty) > 0))) return void (problem = optionText.quantityInvalid);
		if (new Set(chosen.map((line) => line.ingredient_id)).size !== chosen.length) return void (problem = optionText.duplicateIngredient);
		onsave({ lines: chosen.map((line) => ({ ingredient_id: line.ingredient_id, qty: String(decimal(line.qty)) })), all_branches: everyBranch });
	}

	function changeBranch(next: string): void {
		ingredients.reset();
		onbranch(next);
	}
</script>

<Modal open title={format(optionText.extraRecipeTitle, { name: target.title })} description={optionText.recipeDescription} size="md" {busy} {onclose}>
	<div class="flex flex-col gap-4">
		<BranchField bind:value={outletId} onchange={changeBranch} />
		{#each lines as line, index (index)}
			<div class="grid items-end gap-2 tablet:grid-cols-[1fr_8rem_auto]">
				<SelectField
					label={format(optionText.ingredientNumber, { number: index + 1 })}
					value={line.ingredient_id}
					options={optionsFor(line.ingredient_id)}
					empty={optionText.chooseIngredient}
					hint={ingredients.problem || undefined}
					onchange={(id) => pick(line, id)}
					onsearch={(text) => ingredients.search(text)}
					onmore={() => ingredients.more()}
					searching={ingredients.searching}
					loadingMore={ingredients.loadingMore}
				/>
				<TextField label={optionText.quantity} inputmode="decimal" bind:value={line.qty} />
				<DeleteButton small onclick={() => (lines = lines.filter((_, position) => position !== index))} />
			</div>
		{/each}
		<Button label={controlText.addIngredient} icon="plus" variant="tertiary" small compact disabled={noIngredients} onclick={() => (lines = [...lines, { ingredient_id: '', qty: '' }])} class="w-fit" />
		{#if canSpread}
			<CheckRow label={optionText.applyToAllBranches} hint={optionText.applyToAllBranchesHint} checked={everyBranch} onchange={() => (everyBranch = !everyBranch)} />
		{/if}
	</div>

	{#if problem || error}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{problem || error}</Banner></div>
	{/if}

	{#snippet footer()}
		<CancelButton disabled={busy} onclick={onclose} />
		<SaveButton busy={busy} onclick={submit} />
	{/snippet}
</Modal>
