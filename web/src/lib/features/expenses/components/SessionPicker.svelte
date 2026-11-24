<script lang="ts">
	import { api, ApiError } from '$lib/api';
	import type { SessionChoice } from '$lib/api/types';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import OptionList from '$lib/components/form/OptionList.svelte';
	import PickerField from '$lib/components/form/PickerField.svelte';
	import DateRangePanel from '$lib/components/filter/DateRangePanel.svelte';
	import SearchBox from '$lib/components/filter/SearchBox.svelte';
	import { DATE_PRESETS, formatRange, presetRange, todayIso, type DateRange } from '$lib/date/range';
	import { formatDateTime } from '$lib/format/datetime';
	import { RemoteChoices } from '$lib/components/form/remote-choices.svelte';
	import { onMount, untrack } from 'svelte';
	import { termText } from '$lib/text/terms';
	import { expenseText } from '$lib/text/expenses';

	let {
		value = $bindable(''),
		start = null,
		outletId,
		noneLabel,
		hint,
		onpick
	}: {
		value?: string;
		/** The session the form was opened from; it starts chosen and stays listed. */
		start?: SessionChoice | null;
		/** The sessions listed are those of this branch; choosing another branch clears the choice. */
		outletId: string;
		noneLabel: string;
		hint?: string;
		/** The whole session chosen, for what the form needs beyond its id. */
		onpick?: (choice: SessionChoice | null) => void;
	} = $props();

	const presets = DATE_PRESETS.filter((preset) => ['today', 'yesterday', 'last7', 'month'].includes(preset.value));

	let open = $state(false);
	let picked = $state<SessionChoice | null>(untrack(() => start));
	let denied = $state(false);
	let search = $state('');
	let range = $state<DateRange | null>(null);
	let calendar = $state(false);
	// Sesi terus bertambah, jadi dicari di server dan dimuat per halaman (kursor) saat daftar digulir.
	const sessions = new RemoteChoices<SessionChoice>(async (query, cursor) => {
		try {
			const found = await api.expenses.sessionChoices({ search: query || undefined, start: range?.from, end: range?.to, outlet_id: outletId || undefined, cursor: cursor ?? undefined });
			return { items: found.items, next: found.next_cursor };
		} catch (problem) {
			if (problem instanceof ApiError && problem.status === 403) denied = true;
			throw problem;
		}
	}, (item) => item.id);
	// Sesi asal formulir tetap tercantum di daftar awal walau di luar halaman pertama.
	const choices = $derived(start && !sessions.items.some((item) => item.id === start.id) && !search.trim() && !range ? [start, ...sessions.items] : sessions.items);

	onMount(() => {
		if (picked) value = picked.id;
	});

	let lastOutlet = untrack(() => outletId);
	$effect(() => {
		const outlet = outletId;
		untrack(() => {
			if (outlet !== lastOutlet) {
				lastOutlet = outlet;
				picked = null;
				value = '';
				onpick?.(null);
			}
			sessions.reset();
		});
	});

	const describe = (item: SessionChoice) => [item.cashier_username, item.shift_code, formatDateTime(item.opened_at)].filter(Boolean).join(' · ');
	const summary = $derived(picked ? describe(picked) : noneLabel);
	const activePreset = $derived(range ? presets.find((preset) => { const found = presetRange(preset.value, todayIso()); return found?.from === range!.from && found?.to === range!.to; })?.value : undefined);

	function setRange(next: DateRange | null): void {
		range = next;
		sessions.refresh();
	}

	function choose(item: SessionChoice | null): void {
		picked = item;
		value = item?.id ?? '';
		onpick?.(item);
		open = false;
	}
</script>

{#if !denied}
	<PickerField label={termText.cashierSession} {summary} chosen={picked !== null} bind:open {hint}>
		<SearchBox bind:value={search} label={expenseText.searchSession} onsearch={(query) => sessions.search(query)} />
		<div class="flex flex-wrap items-center gap-1.5">
			<Button label={expenseText.newest} active={range === null} onclick={() => setRange(null)} />
			{#each presets as preset (preset.value)}
				<Button label={preset.label} active={activePreset === preset.value} onclick={() => setRange(presetRange(preset.value, todayIso()))} />
			{/each}
			<Button label={range && !activePreset ? formatRange(range) : expenseText.chooseDate} icon="calendar" active={calendar || (range !== null && !activePreset)} onclick={() => (calendar = !calendar)} />
		</div>
		{#if calendar}
			<div class="rounded-lg border border-slate-200 bg-white p-2">
				<DateRangePanel
					value={range}
					reach="past"
					onselect={(next) => {
						setRange(next);
						calendar = false;
					}}
				/>
			</div>
		{/if}
		<OptionList
			label={expenseText.sessionsTitle}
			items={choices}
			key={(item) => item.id}
			selected={(item) => value === item.id}
			onchoose={choose}
			none={{ label: noneLabel, selected: value === '', onchoose: () => choose(null) }}
			empty={sessions.problem || expenseText.noSessionMatch}
			searching={sessions.searching}
			loadingMore={sessions.loadingMore}
			onmore={() => sessions.more()}
		>
			{#snippet option(item)}
				<span class="truncate">{describe(item)}</span>
				{#if item.running}<Badge tone="success">{termText.running}</Badge>{:else}<Badge tone="neutral">{termText.closed}</Badge>{/if}
			{/snippet}
		</OptionList>
	</PickerField>
{/if}
