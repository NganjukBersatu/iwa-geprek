<script lang="ts" generics="T">
	import { tick, type Snippet } from 'svelte';
	import ProgressLine from '$lib/components/motion/ProgressLine.svelte';
	import Skeleton from '$lib/components/skeleton/Skeleton.svelte';

	/** The choices inside a PickerField; the text below the list says why it is empty. */
	let {
		label,
		items,
		key,
		selected,
		onchoose,
		none,
		empty,
		option,
		searching = false,
		loadingMore = false,
		onmore
	}: {
		/** Names the list for screen readers. */
		label: string;
		items: T[];
		key: (item: T) => string;
		selected: (item: T) => boolean;
		onchoose: (item: T) => void;
		/** A first choice that clears the pick, when the field may stay empty. */
		none?: { label: string; selected: boolean; onchoose: () => void };
		/** Shown when there is no item and nothing is loading: a failure or no match. */
		empty: string;
		option: Snippet<[T]>;
		/** Hasil cari sedang ditunggu: daftar diganti kerangka di bawah garis progres. */
		searching?: boolean;
		/** Halaman berikutnya sedang dimuat: kerangka di ujung bawah daftar dan garis progres. */
		loadingMore?: boolean;
		/** Dipanggil saat daftar digulir mendekati akhir, supaya pemanggil memuat halaman berikutnya. */
		onmore?: () => void;
	} = $props();

	// Jarak dari ujung bawah daftar saat halaman berikutnya mulai diminta, kira-kira tiga baris.
	const MORE_BEFORE_PX = 100;
	const SEARCH_SKELETON_ROWS = 3;
	const MORE_SKELETON_ROWS = 2;
	const row = 'flex min-h-0 w-full items-center justify-between gap-2 rounded-lg px-3 py-2 text-left text-sm hover:bg-white';

	let list = $state<HTMLUListElement | null>(null);

	function nearEnd(): void {
		if (onmore && list && list.scrollTop + list.clientHeight >= list.scrollHeight - MORE_BEFORE_PX) onmore();
	}

	// Daftar yang belum cukup panjang untuk digulir langsung meminta halaman berikutnya.
	$effect(() => {
		if (!onmore || searching || items.length === 0) return;
		void tick().then(nearEnd);
	});
</script>

<div class="relative">
	<ul bind:this={list} onscroll={nearEnd} class="flex max-h-56 flex-col gap-1 overflow-y-auto" role="listbox" aria-label={label} aria-busy={searching || loadingMore}>
		{#if none}
			<li>
				<button type="button" role="option" aria-selected={none.selected} onclick={none.onchoose} class="{row} {none.selected ? 'bg-white font-semibold text-brand' : 'text-slate-600'}">{none.label}</button>
			</li>
		{/if}
		{#if searching}
			{#each { length: SEARCH_SKELETON_ROWS } as _, line (line)}
				<li role="presentation" class="px-1 py-1"><Skeleton class="h-7 w-full" /></li>
			{/each}
		{:else}
			{#each items as item (key(item))}
				<li>
					<button type="button" role="option" aria-selected={selected(item)} onclick={() => onchoose(item)} class="{row} {selected(item) ? 'bg-white font-semibold text-brand' : 'text-slate-700'}">
						{@render option(item)}
					</button>
				</li>
			{:else}
				<li class="px-3 py-3 text-center text-xs text-slate-500">{empty}</li>
			{/each}
			{#if loadingMore}
				{#each { length: MORE_SKELETON_ROWS } as _, line (line)}
					<li role="presentation" class="px-1 py-1"><Skeleton class="h-7 w-full" /></li>
				{/each}
			{/if}
		{/if}
	</ul>
	{#if searching || loadingMore}<ProgressLine />{/if}
</div>
