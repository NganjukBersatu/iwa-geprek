<script lang="ts">
	import { api } from '$lib/api';
	import type { BatchUser } from '$lib/api/types';
	import IconButton from '$lib/components/button/IconButton.svelte';
	import SearchBox from '$lib/components/filter/SearchBox.svelte';
	import OptionList from '$lib/components/form/OptionList.svelte';
	import PickerField from '$lib/components/form/PickerField.svelte';
	import { byPage, RemoteChoices } from '$lib/components/form/remote-choices.svelte';
	import { whenChanged } from '$lib/stores/when-changed.svelte';
	import { batchText } from '$lib/text/batches';
	import { format } from '$lib/text/format';

	let { picked = $bindable<BatchUser[]>([]), outletId }: { picked?: BatchUser[]; outletId: string } = $props();

	const LIMIT = 30;

	let open = $state(false);
	let search = $state('');
	let choicesFor = '';
	// Searched and loaded by page on the server, so any employee is reachable however many there are.
	const choices = new RemoteChoices<BatchUser>(
		byPage(LIMIT, (query, page) => api.batches.userOptions({ outlet_id: outletId, q: query || undefined, page, size: LIMIT }).then((found) => found.items)),
		(person) => person.id
	);

	// Another branch has other employees, so the picking starts again when the branch changes; the first branch of an edit keeps its recipients.
	whenChanged(
		() => outletId,
		(branchId) => {
			if (choicesFor !== '' && choicesFor !== branchId) picked = [];
			choicesFor = branchId;
			if (branchId) choices.reset();
		}
	);

	const isPicked = (person: BatchUser): boolean => picked.some((item) => item.id === person.id);
	const toggle = (person: BatchUser) => (picked = isPicked(person) ? picked.filter((item) => item.id !== person.id) : [...picked, person]);
</script>

<PickerField label={batchText.userPicker} summary={picked.length > 0 ? format(batchText.userPickerSummary, { count: picked.length }) : batchText.userPickerEmpty} chosen={picked.length > 0} bind:open>
	<SearchBox bind:value={search} placeholder={batchText.userSearchPlaceholder} label={batchText.userSearchLabel} onsearch={(query) => choices.search(query)} />
	<OptionList
		label={batchText.userListLabel}
		items={choices.items}
		key={(person) => person.id}
		selected={isPicked}
		onchoose={toggle}
		empty={choices.problem || batchText.userNone}
		searching={choices.searching}
		loadingMore={choices.loadingMore}
		onmore={() => choices.more()}
	>
		{#snippet option(person)}
			<span class="flex min-w-0 items-center gap-2">
				<i class="ti ti-check shrink-0 text-base {isPicked(person) ? 'text-brand' : 'opacity-0'}" aria-hidden="true"></i>
				<span class="truncate">{person.name}</span>
			</span>
			<span class="shrink-0 text-xs text-slate-500">{person.role_name ?? ''}</span>
		{/snippet}
	</OptionList>
</PickerField>

{#if picked.length > 0}
	<ul class="mt-2 flex flex-wrap gap-1.5" aria-label={batchText.userPicked}>
		{#each picked as person (person.id)}
			<li class="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-white py-0.5 pl-3 pr-1 text-xs font-semibold text-slate-700">
				{person.name}
				<IconButton icon="x" label={format(batchText.userRelease, { name: person.name })} onclick={() => toggle(person)} />
			</li>
		{/each}
	</ul>
{/if}
