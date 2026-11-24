<script lang="ts">
	import { api } from '$lib/api';
	import type { MenuItem } from '$lib/api/types';
	import SearchBox from '$lib/components/filter/SearchBox.svelte';
	import OptionList from '$lib/components/form/OptionList.svelte';
	import PickerField from '$lib/components/form/PickerField.svelte';
	import { byPage, RemoteChoices } from '$lib/components/form/remote-choices.svelte';
	import { controlText } from '$lib/text/controls';

	/** Memilih satu menu yang dicari dan dimuat per halaman di server, sehingga menu mana pun terjangkau. */
	let { label = controlText.menuLabel, onchoose }: { label?: string; onchoose: (menu: MenuItem) => void } = $props();

	const LIMIT = 30;

	let open = $state(false);
	let search = $state('');
	let picked = $state<MenuItem | null>(null);
	const choices = new RemoteChoices<MenuItem>(
		byPage(LIMIT, (query, page) => api.menu.list({ search: query || undefined, page, size: LIMIT }).then((found) => found.items)),
		(item) => item.id
	);

	function choose(item: MenuItem): void {
		picked = item;
		open = false;
		onchoose(item);
	}
</script>

<PickerField {label} summary={picked ? picked.name : controlText.chooseMenu} chosen={picked !== null} bind:open>
	<SearchBox bind:value={search} placeholder={controlText.menuName} label={controlText.searchMenu} onsearch={(query) => choices.search(query)} />
	<OptionList
		label={controlText.menuList}
		items={choices.items}
		key={(item) => item.id}
		selected={(item) => picked?.id === item.id}
		onchoose={choose}
		empty={choices.problem || controlText.noMenuMatch}
		searching={choices.searching}
		loadingMore={choices.loadingMore}
		onmore={() => choices.more()}
	>
		{#snippet option(item)}
			<span class="truncate">{item.name}</span>
		{/snippet}
	</OptionList>
</PickerField>
