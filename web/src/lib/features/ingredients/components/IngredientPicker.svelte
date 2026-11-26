<script lang="ts">
	import { api } from '$lib/api';
	import type { Ingredient } from '$lib/api/types';
	import SearchBox from '$lib/components/filter/SearchBox.svelte';
	import OptionList from '$lib/components/form/OptionList.svelte';
	import PickerField from '$lib/components/form/PickerField.svelte';
	import { byPage, RemoteChoices } from '$lib/components/form/remote-choices.svelte';
	import { formatNumber } from '$lib/format/currency';
	import { whenChanged } from '$lib/stores/when-changed.svelte';
	import { termText } from '$lib/text/terms';
	import { ingredientText } from '$lib/text/ingredients';

	let {
		value = $bindable(''),
		label = termText.ingredient,
		picked = $bindable<Ingredient | null>(null),
		outletId,
		indirect
	}: {
		value?: string;
		label?: string;
		picked?: Ingredient | null;
		outletId: string;
		/** Hanya bahan tidak langsung (true) atau hanya yang dipotong resep (false); kosong berarti keduanya. */
		indirect?: boolean;
	} = $props();

	const LIMIT = 30;

	let open = $state(false);
	let search = $state('');
	// Dicari dan dimuat per halaman di server, supaya bahan mana pun terjangkau berapa pun jumlahnya.
	const choices = new RemoteChoices<Ingredient>(
		byPage(LIMIT, (query, page) => api.ingredients.list({ search: query || undefined, page, size: LIMIT, outlet_id: outletId, indirect }).then((found) => found.items)),
		(item) => item.id
	);

	// Another branch has other ingredients, so the pick starts again whenever the branch changes.
	whenChanged(
		() => outletId,
		() => {
			picked = null;
			value = '';
			choices.reset();
		}
	);

	function choose(item: Ingredient): void {
		picked = item;
		value = item.id;
		open = false;
	}
</script>

<PickerField {label} summary={picked ? `${picked.name} (${picked.unit})` : ingredientText.chooseIngredient} chosen={picked !== null} bind:open>
	<SearchBox bind:value={search} placeholder={ingredientText.nameOrCategory} label={ingredientText.search} onsearch={(query) => choices.search(query)} />
	<OptionList
		label={ingredientText.listTitle}
		items={choices.items}
		key={(item) => item.id}
		selected={(item) => value === item.id}
		onchoose={choose}
		empty={choices.problem || ingredientText.noMatch}
		searching={choices.searching}
		loadingMore={choices.loadingMore}
		onmore={() => choices.more()}
	>
		{#snippet option(item)}
			<span class="min-w-0 wrap-break-word">{item.name}</span>
			<span class="shrink-0 text-xs text-slate-500">{formatNumber(item.balance)} {item.unit}</span>
		{/snippet}
	</OptionList>
</PickerField>
