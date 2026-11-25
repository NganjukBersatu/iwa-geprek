<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import type { Snippet } from 'svelte';
	import { viewport } from '$lib/platform/viewport.svelte';
	import BottomBar from './BottomBar.svelte';
	import type { BottomBarItem } from './types';
	import Rail from './Rail.svelte';
	import { t } from '$lib/text/t';

	/** Kerangka halaman setelah login: bilah bawah di HP dan rail kiri di layar lebar. */
	let {
		items,
		onLogout,
		banner,
		children
	}: {
		items: readonly BottomBarItem[];
		onLogout: () => void;
		/** Pita keadaan sistem di atas isi halaman, misalnya mode demo; disusun oleh halaman. */
		banner?: Snippet;
		children: Snippet;
	} = $props();

	let collapsed = $state(false);
</script>

{#if viewport.isWide}
	<div class="flex h-dvh w-full bg-background" use:dynamicStyle={{ 'padding-top': 'var(--safe-top)', 'padding-bottom': 'var(--safe-bottom)' }}>
		<aside
			class="m-2 shrink-0 overflow-hidden rounded-card bg-primary"
			use:dynamicStyle={{ width: `${collapsed ? 72 : 224}px`, transition: 'width var(--effect-standard) var(--ease-standard)' }}
		>
			<Rail
				logo="/brand-logo.png"
				logoDescription={t('shell_logo_description')}
				title={t('shell_rail_title')}
				subtitle={t('shell_rail_subtitle')}
				{items}
				{collapsed}
				onToggle={() => (collapsed = !collapsed)}
				collapseDescription={t('shell_rail_collapse')}
				expandDescription={t('shell_rail_expand')}
				logoutLabel={t('nav_logout')}
				{onLogout}
			/>
		</aside>
		<main class="flex h-full min-w-0 flex-1 flex-col">
			{@render banner?.()}
			<div class="relative min-h-0 flex-1">{@render children()}</div>
		</main>
	</div>
{:else}
	<div class="flex h-dvh w-full flex-col bg-background">
		<main class="flex min-h-0 w-full flex-1 flex-col" use:dynamicStyle={{ 'padding-top': 'var(--safe-top)' }}>
			{@render banner?.()}
			<div class="relative min-h-0 flex-1">{@render children()}</div>
		</main>
		{#if !viewport.keyboardOpen}<BottomBar {items} />{/if}
	</div>
{/if}
