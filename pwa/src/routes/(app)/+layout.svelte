<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import type { Snippet } from 'svelte';
	import AppShell from '$lib/components/layout/AppShell.svelte';
	import type { BottomBarItem } from '$lib/components/layout/types';
	import { current } from '$lib/auth/current.svelte';
	import NetworkGate from '$lib/features/network/NetworkGate.svelte';
	import NoticeRoute from '$lib/features/notices/NoticeRoute.svelte';
	import PermissionGateRoute from '$lib/features/permission/PermissionGateRoute.svelte';
	import UpdateRoute from '$lib/features/release/UpdateRoute.svelte';
	import WhatsNewRoute from '$lib/features/release/WhatsNewRoute.svelte';
	import { t } from '$lib/text/t';

	let { children }: { children: Snippet } = $props();

	let releaseShown = $state(false);
	// Izin diminta lebih dulu; ringkasan pembaruan, ajakan memperbarui, dan pemberitahuan menunggu sampai panel izin tertutup, satu lembar sekali tampil.
	let permissionClear = $state(false);

	// Halaman yang dibuka dari Lainnya tetap menyalakan tab Lainnya; Kehadiran bisa dibuka dari Dashboard dan menyalakan tab asalnya.
	const MORE_PAGES = ['/tasks', '/sop', '/leave-overtime', '/performance', '/presence', '/activity', '/about'];

	const activeTab = $derived.by(() => {
		const path = page.url.pathname;
		if (path.startsWith('/presence') && page.url.searchParams.get('from') === 'dashboard') return '/dashboard';
		if (path.startsWith('/more') || MORE_PAGES.some((entry) => path.startsWith(entry))) return '/more';
		return ['/dashboard', '/schedule', '/attendance', '/profile'].find((entry) => path.startsWith(entry)) ?? '/dashboard';
	});

	const items = $derived<BottomBarItem[]>([
		{ label: t('nav_dashboard'), icon: 'Dashboard', href: '/dashboard', selected: activeTab === '/dashboard' },
		{ label: t('nav_schedule'), icon: 'Calendar', href: '/schedule', selected: activeTab === '/schedule' },
		{ label: t('nav_attendance'), icon: 'CalendarCheck', href: '/attendance', selected: activeTab === '/attendance', prominent: true },
		{ label: t('nav_profile'), icon: 'UserCircle', href: '/profile', selected: activeTab === '/profile' },
		{ label: t('nav_more'), icon: 'More', href: '/more', selected: activeTab === '/more' }
	]);

	function signOut(): void {
		current.signOut();
		void goto('/login', { replaceState: true });
	}
</script>

{#if current.session}
	<PermissionGateRoute bind:clear={permissionClear}>
		<NetworkGate>
			<AppShell {items} onLogout={signOut}>
				{@render children()}
			</AppShell>
		</NetworkGate>
		{#if permissionClear}
			<WhatsNewRoute onSessionExpired={signOut} bind:done={releaseShown} />
			<UpdateRoute />
			{#if releaseShown}<NoticeRoute onSessionExpired={signOut} />{/if}
		{/if}
	</PermissionGateRoute>
{/if}
