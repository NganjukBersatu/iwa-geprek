<script lang="ts">
	import { Menu, Portal } from '@skeletonlabs/skeleton-svelte';
	import { controlSize, secondaryStyle } from './button-style';
	import type { Action } from './types';

	let {
		label,
		icon,
		items,
		disabled = false,
		hint,
		compact = false,
		variant = 'secondary',
		iconOnly = false
	}: {
		label: string;
		icon?: string;
		items: Action[];
		disabled?: boolean;
		hint?: string;
		compact?: boolean;
		variant?: 'primary' | 'secondary';
		iconOnly?: boolean;
	} = $props();

	const style = $derived(
		variant === 'primary'
			? 'bg-brand text-white hover:bg-brand-hover data-[state=open]:bg-brand-hover'
			: `${secondaryStyle} data-[state=open]:border-brand data-[state=open]:bg-brand-page data-[state=open]:text-brand`
	);
</script>

<Menu onSelect={(details) => items.find((item) => item.label === details.value)?.onclick()}>
	<Menu.Trigger
		{disabled}
		title={disabled && hint ? hint : label}
		aria-label={label}
		class="btn btn-sm shrink-0 font-semibold hover:brightness-100 disabled:opacity-50 {controlSize} {iconOnly ? 'pointer-fine:w-8 px-0' : ''} {style}"
	>
		{#if icon}
			<i class="ti ti-{icon} text-sm" aria-hidden="true"></i>
		{/if}
		{#if !iconOnly}
			<span class={compact ? 'hidden tablet:inline' : ''}>{label}</span>
			<i class="ti ti-chevron-down text-sm" aria-hidden="true"></i>
		{/if}
	</Menu.Trigger>
	<Portal>
		<Menu.Positioner>
			<Menu.Content class="z-40 w-max min-w-40 max-w-60 rounded-lg border border-brand-line bg-white p-1 shadow-lg outline-none">
				{#each items as item (item.label)}
					<Menu.Item
						value={item.label}
						disabled={item.disabled}
						class="flex w-full cursor-pointer items-center justify-start gap-2 rounded-md px-2 py-1.5 text-left text-control font-medium text-brand-ink data-highlighted:bg-brand-soft data-disabled:opacity-50"
					>
						<i class="ti ti-{item.icon} w-4 shrink-0 text-center text-base" aria-hidden="true"></i>
						<span class="flex min-w-0 flex-col items-start text-left">
							{item.label}
							{#if item.description}<span class="text-note font-normal text-brand-muted">{item.description}</span>{/if}
						</span>
					</Menu.Item>
				{/each}
			</Menu.Content>
		</Menu.Positioner>
	</Portal>
</Menu>
