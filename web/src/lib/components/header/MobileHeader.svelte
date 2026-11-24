<script lang="ts">
	import type { SidebarBrand } from '$lib/components/sidebar/types';
	import { controlText } from '$lib/text/controls';

	let {
		brand,
		menuOpen = $bindable(false)
	}: {
		brand: SidebarBrand;
		menuOpen?: boolean;
	} = $props();
</script>

<header data-scroll-head data-mobile-header class="flex h-(--topbar-height) shrink-0 items-center border-b border-brand-line/50 bg-brand-soft px-3 tablet:hidden">
	<button
		type="button"
		onclick={() => (menuOpen = !menuOpen)}
		class="flex size-9 shrink-0 items-center justify-center rounded-md text-slate-500 hover:bg-brand-soft hover:text-brand"
		aria-label={menuOpen ? controlText.closeMenu : controlText.openMenu}
	>
		<i class="ti text-[1.25rem] {menuOpen ? 'ti-x' : 'ti-menu-2'}" aria-hidden="true"></i>
	</button>

	<div class="ml-2 flex items-center gap-2">
		<img src={brand.logo} alt={brand.logoAlt} width="300" height="396" class="h-auto w-6 shrink-0" />
		<div class="whitespace-nowrap">
			<p class="text-sm font-semibold leading-none text-slate-800">{brand.title}</p>
			<p class="mt-0.5 text-xs font-semibold tracking-wider text-brand">{brand.subtitle}</p>
		</div>
	</div>
</header>
