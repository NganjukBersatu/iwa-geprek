<script lang="ts">
	import { goto } from '$app/navigation';
	import { current } from '$lib/auth/current.svelte';
	import SubPage from '$lib/components/layout/SubPage.svelte';
	import TaskScreen from '$lib/features/tasks/components/TaskScreen.svelte';
	import { t } from '$lib/text/t';

	function expired(): void {
		current.signOut();
		void goto('/login', { replaceState: true });
	}
</script>

<SubPage title={t('nav_tasks')} backHref="/more"><TaskScreen onSessionExpired={expired} /></SubPage>
