<script lang="ts">
	import SidebarItem from './SidebarItem.svelte';
	import type { NavGroup } from './types';

	let {
		group,
		current,
		open,
		compact = false,
		mobile = false,
		ontoggle,
		onnavigate
	}: {
		group: NavGroup;
		/** The address of the one entry shown as current. */
		current: string | null;
		open: boolean;
		compact?: boolean;
		mobile?: boolean;
		ontoggle: () => void;
		onnavigate?: () => void;
	} = $props();

	const groupActive = $derived(group.items.some((leaf) => leaf.href === current));
	const expanded = $derived(open && !compact);
	const rowClass = $derived(
		groupActive && !expanded
			? 'bg-brand font-semibold text-brand-on'
			: groupActive
				? 'font-semibold text-brand-ink hover:bg-brand-tint'
				: 'text-brand-ink hover:bg-brand-tint'
	);
</script>

<div>
	<button
		type="button"
		onclick={ontoggle}
		title={group.label}
		aria-expanded={expanded}
		class="flex w-full items-center gap-3 rounded-lg px-3 text-nav outline-none transition-colors focus-visible:ring-2 focus-visible:ring-brand/40 motion-reduce:transition-none {compact ? 'justify-center' : ''} {mobile ? 'py-2.5' : 'py-2'} {rowClass}"
	>
		<i class="ti {group.icon} text-xl" aria-hidden="true"></i>
		{#if !compact}
			<span class="min-w-0 text-left">{group.label}</span>
			<i class="ti ti-chevron-down ml-auto text-sm transition-transform duration-200 motion-reduce:transition-none {expanded ? 'rotate-180' : ''}" aria-hidden="true"></i>
		{/if}
	</button>

	<div
		class="grid transition-[grid-template-rows] duration-200 motion-reduce:transition-none {expanded ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'}"
		inert={!expanded}
	>
		<div class="overflow-hidden">
			<div class="relative ml-5 mt-1 flex flex-col gap-0.5 py-1">
				<div class="absolute inset-y-1 left-0 w-px bg-brand-line/60"></div>
				{#each group.items as leaf (leaf.href)}
					<SidebarItem {leaf} active={leaf.href === current} {mobile} {onnavigate} />
				{/each}
			</div>
		</div>
	</div>
</div>
