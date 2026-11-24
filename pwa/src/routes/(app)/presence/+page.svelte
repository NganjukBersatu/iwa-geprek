<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { current } from '$lib/auth/current.svelte';
	import SubPage from '$lib/components/layout/SubPage.svelte';
	import PresenceView from '$lib/features/presence/components/PresenceView.svelte';
	import { t } from '$lib/text/t';

	// Kembali selalu ke halaman asalnya: Dashboard atau Lainnya.
	const backHref = $derived(page.url.searchParams.get('from') === 'dashboard' ? '/dashboard' : '/more');

	function expired(): void {
		current.signOut();
		void goto('/login', { replaceState: true });
	}
</script>

<SubPage title={t('nav_presence')} {backHref}><PresenceView onSessionExpired={expired} /></SubPage>
