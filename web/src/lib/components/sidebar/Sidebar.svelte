<script lang="ts">
	import { onMount, untrack, type Snippet } from 'svelte';
	import { access } from '$lib/auth/access.svelte';
	import { revealActive } from '$lib/motion/actions';
	import SidebarGroup from './SidebarGroup.svelte';
	import SidebarTop from './SidebarTop.svelte';
	import {
		activeHref,
		isGroup,
		type NavEntry,
		type SidebarBrand,
		type SidebarProfile
	} from './types';
	import { controlText } from '$lib/text/controls';

	let {
		entries,
		brand,
		path,
		collapsed = $bindable(false),
		mobileOpen = $bindable(false),
		profile,
		onsignout,
		top,
		storageKey = 'sidebar'
	}: {
		entries: NavEntry[];
		brand: SidebarBrand;
		path: string;
		collapsed?: boolean;
		mobileOpen?: boolean;
		profile?: SidebarProfile;
		onsignout?: () => void;
		top?: Snippet<[boolean]>;
		storageKey?: string;
	} = $props();

	// Entries the account may not open are left out, and a group left with none goes with them.
	const shown = $derived(
		entries.flatMap((entry): NavEntry[] => {
			if (!isGroup(entry)) return access.opens(entry.screen) ? [entry] : [];
			const items = entry.items.filter((leaf) => access.opens(leaf.screen) && (!leaf.area || access.allows(leaf.area)));
			return items.length > 0 ? [{ ...entry, items }] : [];
		})
	);

	const COLLAPSED_KEY = $derived(`${storageKey}_collapsed`);
	const GROUPS_KEY = $derived(`${storageKey}_groups`);

	let openGroups = $state<Record<string, boolean>>({});
	let hydrated = $state(false);
	let photoBroken = $state(false);

	onMount(() => {
		try {
			const saved = localStorage.getItem(COLLAPSED_KEY);
			collapsed = saved === null ? !window.matchMedia('(min-width: 64rem)').matches : saved === '1';
			openGroups = JSON.parse(localStorage.getItem(GROUPS_KEY) ?? '{}') ?? {};
		} catch {}
		hydrated = true;
	});

	$effect(() => {
		if (!hydrated) return;
		try {
			localStorage.setItem(COLLAPSED_KEY, collapsed ? '1' : '0');
			localStorage.setItem(GROUPS_KEY, JSON.stringify(openGroups));
		} catch {}
	});

	$effect(() => {
		const active = shown.find((e) => isGroup(e) && e.items.some((leaf) => leaf.href === current));
		if (!active || !isGroup(active)) return;
		if (!untrack(() => openGroups)[active.key]) {
			openGroups = { ...untrack(() => openGroups), [active.key]: true };
		}
	});

	$effect(() => {
		profile?.photoUrl;
		photoBroken = false;
	});

	function toggleGroup(key: string): void {
		if (collapsed) {
			collapsed = false;
			openGroups = { ...openGroups, [key]: true };
			return;
		}
		openGroups = { ...openGroups, [key]: !openGroups[key] };
	}

	function closeMobile(): void {
		mobileOpen = false;
	}

	/** The one entry shown as current, so a page inside Barang Masuk does not also light Daftar Bahan. */
	const current = $derived(activeHref(shown, path));
	const profileActive = $derived(!!profile && path.startsWith(profile.href));
</script>

{#snippet navList(mobile: boolean)}
	{@const compact = collapsed && !mobile}
	{#each shown as entry (isGroup(entry) ? entry.key : entry.href)}
		{#if isGroup(entry)}
			<SidebarGroup
				group={entry}
				{current}
				open={!!openGroups[entry.key]}
				{compact}
				{mobile}
				ontoggle={() => toggleGroup(entry.key)}
				onnavigate={closeMobile}
			/>
		{:else}
			<SidebarTop {entry} active={entry.href === current} {compact} {mobile} onnavigate={closeMobile} />
		{/if}
	{/each}
{/snippet}

{#snippet signOutButton(mobile: boolean)}
	{#if onsignout}
		{@const compact = collapsed && !mobile}
		<button
			type="button"
			title={controlText.signOut}
			onclick={onsignout}
			class="flex w-full min-h-0 items-center gap-3 rounded-lg px-3 text-nav text-brand-ink transition-colors hover:bg-danger-50 hover:text-danger-700 motion-reduce:transition-none {compact ? 'justify-center' : ''} {mobile ? 'py-2.5' : 'py-2'}"
		>
			<i class="ti ti-logout text-xl" aria-hidden="true"></i>
			{#if !compact}<span class="whitespace-nowrap">{controlText.signOut}</span>{/if}
		</button>
	{/if}
{/snippet}

{#snippet profileLink(mobile: boolean)}
	{#if profile}
		{@const compact = collapsed && !mobile}
		<a
			href={profile.href}
			title={profile.label}
			onclick={closeMobile}
			class="flex items-center gap-3 rounded-md px-3 text-nav transition-colors {mobile ? 'py-2.5' : 'py-2'} {profileActive ? 'bg-brand font-semibold text-brand-on' : 'text-brand-ink hover:bg-brand-tint'}"
		>
			<span class="flex size-5 shrink-0 items-center justify-center">
				{#if profile.photoUrl && !photoBroken}
					<img src={profile.photoUrl} alt="" class="size-6 rounded-full object-cover" onerror={() => (photoBroken = true)} />
				{:else}
					<i class="ti {profile.icon}" aria-hidden="true"></i>
				{/if}
			</span>
			{#if !compact}
				<span class="min-w-0 flex-1">
					<span class="block whitespace-nowrap">{profile.label}</span>
					{#if profile.subtitle}
						<span class="block text-xs font-normal {profileActive ? 'text-brand-on/80' : 'text-brand-muted'}">{profile.subtitle}</span>
					{/if}
				</span>
			{/if}
		</a>
	{/if}
{/snippet}

<aside
	class="hidden min-h-0 border-r border-brand-tint bg-brand-page transition-all duration-200 tablet:flex tablet:flex-col {collapsed ? 'tablet:w-(--sidebar-width-collapsed)' : 'tablet:w-(--sidebar-width)'}"
>
	<div class="flex items-center justify-between border-b border-brand-tint px-4 py-5">
		<div class="flex items-center gap-2.5 overflow-hidden">
			<span class="flex h-11 w-9 shrink-0 items-center justify-center rounded-lg border border-brand-tint bg-white">
				<img src={brand.logo} alt={brand.logoAlt} width="300" height="396" class="h-auto w-7" />
			</span>
			{#if !collapsed}
				<div class="whitespace-nowrap">
					<p class="text-sm font-semibold leading-none text-brand-ink">{brand.title}</p>
					<p class="mt-0.5 text-xs font-semibold tracking-wider text-brand">{brand.subtitle}</p>
				</div>
			{/if}
		</div>
		<button
			type="button"
			onclick={() => (collapsed = !collapsed)}
			class="flex size-7 shrink-0 items-center justify-center rounded-md text-brand-ink hover:bg-brand-tint hover:text-brand {collapsed ? 'hidden' : ''}"
			aria-label={controlText.collapseSidebar}
		>
			<i class="ti ti-chevron-left" aria-hidden="true"></i>
		</button>
	</div>

	{#if collapsed}
		<button
			type="button"
			onclick={() => (collapsed = false)}
			class="mx-2 mt-1 flex size-8 items-center justify-center self-center rounded-md text-brand-ink hover:bg-brand-tint hover:text-brand"
			aria-label={controlText.expandSidebar}
		>
			<i class="ti ti-chevron-right" aria-hidden="true"></i>
		</button>
	{/if}

	{#if top && !collapsed}
		<div class="border-b border-brand-tint px-3 py-2.5">
			{@render top(false)}
		</div>
	{/if}

	<nav class="sidebar-scroll flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto p-2">
		{@render navList(false)}
	</nav>

	{#if profile}
		<div class="mt-auto flex flex-col gap-0.5 border-t border-brand-tint p-2">
			{@render profileLink(false)}
			{@render signOutButton(false)}
		</div>
	{/if}
</aside>

{#if mobileOpen}
	<div class="fixed inset-x-0 bottom-0 top-(--topbar-height) z-50 tablet:hidden">
		<button type="button" class="absolute inset-0 bg-black/35" aria-label={controlText.closeMenu} onclick={closeMobile}></button>

		<aside class="absolute inset-y-0 left-0 flex w-[68vw] max-w-80 flex-col bg-brand-page shadow-2xl">
			<nav use:revealActive class="sidebar-scroll min-h-0 flex-1 overflow-y-auto p-3">
				{#if top}
					<div class="mb-3 border-b border-brand-tint pb-3">
						{@render top(true)}
					</div>
				{/if}

				<div class="flex flex-col gap-1">
					{@render navList(true)}
				</div>

				{#if profile}
					<div class="mt-3 flex flex-col gap-0.5 border-t border-brand-tint pt-3">
						{@render profileLink(true)}
						{@render signOutButton(true)}
					</div>
				{/if}
			</nav>
		</aside>
	</div>
{/if}

<style>
	.sidebar-scroll {
		scrollbar-width: thin;
		scrollbar-color: var(--color-brand-line) transparent;
	}

	.sidebar-scroll::-webkit-scrollbar {
		width: 6px;
	}

	.sidebar-scroll::-webkit-scrollbar-track {
		background: transparent;
	}

	.sidebar-scroll::-webkit-scrollbar-thumb {
		background-color: var(--color-brand-line);
		border-radius: 9999px;
	}

	.sidebar-scroll::-webkit-scrollbar-thumb:hover {
		background-color: var(--color-brand-accent);
	}
</style>
