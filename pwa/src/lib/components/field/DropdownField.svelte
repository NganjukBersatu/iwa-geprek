<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import PickerField from './PickerField.svelte';
	import TextField from './TextField.svelte';
	import type { DropdownOption } from './types';

	const LIST_MAX_HEIGHT = 220;

	/** Kolom pilihan yang membuka daftar di tempatnya; memilih langsung memanggil [onSelect] dan menutup daftar, dan bila [searchLabel] diisi daftar bisa disaring dengan mengetik. */
	let {
		label,
		options,
		selectedKey,
		onSelect,
		searchLabel,
		emptyText = ''
	}: {
		label: string;
		options: readonly DropdownOption[];
		selectedKey: string | null;
		onSelect: (key: string | null) => void;
		searchLabel?: string;
		emptyText?: string;
	} = $props();

	let open = $state(false);
	let query = $state('');

	const selected = $derived(options.find((option) => option.key === selectedKey) ?? options[0]);
	const shown = $derived(query.trim() === '' ? options : options.filter((option) => option.label.toLowerCase().includes(query.trim().toLowerCase())));
</script>

<div class="flex w-full flex-col gap-2">
	<PickerField
		{label}
		valueText={selected?.label ?? ''}
		icon={open ? 'ChevronUp' : 'ChevronDown'}
		onclick={() => {
			open = !open;
			query = '';
		}}
	/>
	{#if open}
		{#if searchLabel}
			<TextField bind:value={query} label={searchLabel}>
				{#snippet trailing()}<span class="pr-3"><AppIcon icon="Search" tint="content-muted" size={20} /></span>{/snippet}
			</TextField>
		{/if}
		<div class="w-full overflow-y-auto rounded-field border border-divider bg-surface" use:dynamicStyle={{ 'max-height': `${LIST_MAX_HEIGHT}px` }}>
			{#if shown.length === 0}
				<p class="text-body m-0 p-3 text-content-muted">{emptyText}</p>
			{/if}
			{#each shown as option (option.key ?? '')}
				{@const isSelected = option.key === selectedKey}
				<button
					type="button"
					onclick={() => {
						onSelect(option.key);
						open = false;
						query = '';
					}}
					class="flex min-h-[var(--space-touch)] w-full items-center gap-2 px-3 {isSelected ? 'bg-selected' : 'bg-surface'}"
				>
					<span class="text-body min-w-0 flex-1 text-start text-content">{option.label}</span>
					{#if isSelected}<AppIcon icon="Check" tint="primary" size={20} />{/if}
				</button>
			{/each}
		</div>
	{/if}
</div>
