<script lang="ts">
	import type { Snippet } from 'svelte';
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import Divider from '$lib/components/feedback/Divider.svelte';
	import type { BottomBarItem } from './types';

	/** Rail kiri untuk layar lebar, di atas latar primary: logo dan judul, butir menu, lalu keluar. */
	let {
		logo,
		logoDescription,
		title,
		subtitle,
		items,
		collapsed,
		onToggle,
		collapseDescription,
		expandDescription,
		logoutLabel,
		onLogout
	}: {
		logo: string;
		logoDescription: string;
		title: string;
		subtitle: string;
		items: readonly BottomBarItem[];
		collapsed: boolean;
		onToggle: () => void;
		collapseDescription: string;
		expandDescription: string;
		logoutLabel: string;
		onLogout: () => void;
	} = $props();
</script>

<div class="flex h-full flex-col">
	{#if collapsed}
		<div class="flex flex-col items-center gap-1 py-3">
			<img src={logo} alt={logoDescription} class="size-9 rounded-field object-cover" />
			<button type="button" onclick={onToggle} aria-label={expandDescription} class="flex size-[var(--space-touch)] items-center justify-center rounded-full">
				<AppIcon icon="ChevronRight" tint="background" size={20} />
			</button>
		</div>
	{:else}
		<div class="flex items-center gap-3 px-3 py-3">
			<img src={logo} alt={logoDescription} class="size-9 rounded-field object-cover" />
			<div class="min-w-0 flex-1">
				<p class="text-body m-0 truncate font-bold text-on-primary">{title}</p>
				<p class="text-label m-0 truncate text-surface-accent">{subtitle}</p>
			</div>
			<button type="button" onclick={onToggle} aria-label={collapseDescription} class="flex size-[var(--space-touch)] items-center justify-center rounded-full">
				<AppIcon icon="ChevronLeft" tint="background" size={20} />
			</button>
		</div>
	{/if}
	<Divider />

	<div class="flex flex-1 flex-col">
		{#each items as item (item.href)}
			{@const color = item.selected ? 'content' : 'background'}
			<a
				href={item.href}
				aria-current={item.selected ? 'page' : undefined}
				class="flex min-h-[var(--space-touch)] w-full items-center rounded-field px-3 py-2 {collapsed ? 'justify-center' : 'gap-3'} {item.selected ? 'bg-surface-accent' : ''}"
			>
				<AppIcon icon={item.icon} tint={color} label={collapsed ? item.label : undefined} />
				{#if !collapsed}
					<span class="text-body min-w-0 flex-1 truncate {item.selected ? 'font-bold text-content' : 'text-background'}">{item.label}</span>
				{/if}
			</a>
		{/each}
	</div>

	<button type="button" onclick={onLogout} class="flex min-h-[var(--space-touch)] w-full items-center rounded-field px-3 py-2 {collapsed ? 'justify-center' : 'gap-3'}">
		<AppIcon icon="Logout" tint="background" label={collapsed ? logoutLabel : undefined} />
		{#if !collapsed}<span class="text-body min-w-0 flex-1 truncate text-background">{logoutLabel}</span>{/if}
	</button>
</div>
