<script lang="ts">
	import { goto } from '$app/navigation';
	import { current } from '$lib/auth/current.svelte';
	import SubPage from '$lib/components/layout/SubPage.svelte';
	import ActivityView from '$lib/features/activity/components/ActivityView.svelte';
	import { t } from '$lib/text/t';

	function expired(): void {
		current.signOut();
		void goto('/login', { replaceState: true });
	}
</script>

<SubPage title={t('nav_activity')} backHref="/more"><ActivityView onSessionExpired={expired} /></SubPage>
