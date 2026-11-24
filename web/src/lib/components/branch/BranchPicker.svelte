<script lang="ts">
	import { format } from '$lib/text/format';
	import { api } from '$lib/api';
	import type { OutletOption } from '$lib/api/types';
	import Modal from '$lib/components/dialog/Modal.svelte';
	import { onDestroy } from 'svelte';
	import { termText } from '$lib/text/terms';
	import { controlText } from '$lib/text/controls';

	let {
		open,
		title = controlText.chooseBranch,
		onselect,
		onclose
	}: {
		open: boolean;
		title?: string;
		onselect: (id: string) => void;
		onclose: () => void;
	} = $props();

	const listId = $props.id();
	const DELAY_MILLISECONDS = 250;
	const SUGGESTIONS = 8;

	let text = $state('');
	let found = $state<OutletOption[]>([]);
	let total = $state(0);
	let active = $state(0);
	let loading = $state(false);
	let failed = $state(false);
	let field = $state<HTMLInputElement | null>(null);
	let timer: ReturnType<typeof setTimeout> | undefined;
	let ticket = 0;

	async function lookup(query: string): Promise<void> {
		const mine = ++ticket;
		loading = true;
		failed = false;
		try {
			const page = await api.outlets.search({ search: query.trim() || undefined, size: SUGGESTIONS });
			if (mine !== ticket) return;
			found = page.items;
			total = page.total;
			active = 0;
		} catch {
			if (mine === ticket) failed = true;
		} finally {
			if (mine === ticket) loading = false;
		}
	}

	// Each opening starts clean, lists the first branches, and puts the cursor in the box.
	$effect(() => {
		if (!open) return;
		text = '';
		void lookup('');
	});

	$effect(() => {
		if (open && field) requestAnimationFrame(() => field?.focus());
	});

	function type(event: Event & { currentTarget: HTMLInputElement }): void {
		text = event.currentTarget.value;
		clearTimeout(timer);
		timer = setTimeout(() => void lookup(text), DELAY_MILLISECONDS);
	}

	function keys(event: KeyboardEvent): void {
		if (event.key === 'ArrowDown') {
			event.preventDefault();
			active = Math.min(active + 1, found.length - 1);
		} else if (event.key === 'ArrowUp') {
			event.preventDefault();
			active = Math.max(active - 1, 0);
		} else if (event.key === 'Enter' && found[active]) {
			event.preventDefault();
			onselect(found[active]!.id);
		}
	}

	onDestroy(() => clearTimeout(timer));
</script>

<Modal {open} {title} size="sm" {onclose}>
	<div class="flex flex-col gap-3">
		<div class="flex min-h-11 items-center gap-2 rounded-md border-2 border-brand bg-white px-3">
			<i class="ti ti-search text-slate-400" aria-hidden="true"></i>
			<input
				bind:this={field}
				type="text"
				role="combobox"
				aria-expanded={found.length > 0}
				aria-controls={listId}
				aria-activedescendant={found[active] ? `${listId}-${active}` : undefined}
				aria-label={controlText.searchBranch}
				autocomplete="off"
				placeholder={controlText.branchPlaceholder}
				value={text}
				oninput={type}
				onkeydown={keys}
				class="min-w-0 flex-1 bg-transparent py-2 text-sm text-slate-800 outline-none placeholder:text-slate-500"
			/>
		</div>
		<ul id={listId} role="listbox" aria-label={termText.branch} class="flex max-h-72 flex-col gap-0.5 overflow-y-auto">
			{#each found as option, index (option.id)}
				<li>
					<button
						type="button"
						id="{listId}-{index}"
						role="option"
						aria-selected={index === active}
						onclick={() => onselect(option.id)}
						class="flex min-h-0 w-full items-center rounded-md px-3 py-2.5 text-left text-sm {index === active ? 'bg-brand-soft font-semibold text-brand-deep' : 'text-slate-700 hover:bg-slate-50'}"
					>
						{option.name}
					</button>
				</li>
			{:else}
				<li class="px-3 py-3 text-center text-xs text-slate-500">{loading ? controlText.searching : failed ? controlText.branchSearchFailed : controlText.noBranchMatch}</li>
			{/each}
		</ul>
		<p class="text-xs text-slate-500">
			{total > found.length ? format(controlText.branchesShown, { shown: found.length, total }) : controlText.pickerKeysHint}
		</p>
	</div>
</Modal>
