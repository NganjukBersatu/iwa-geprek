<script lang="ts">
	import { goto } from '$app/navigation';
	import { current } from '$lib/auth/current.svelte';
	import SubPage from '$lib/components/layout/SubPage.svelte';
	import LeaveOvertimePage from '$lib/features/leaveovertime/components/LeaveOvertimePage.svelte';
	import { t } from '$lib/text/t';

	function expired(): void {
		current.signOut();
		void goto('/login', { replaceState: true });
	}
</script>

<SubPage title={t('nav_leave_overtime')} backHref="/more"><LeaveOvertimePage onSessionExpired={expired} /></SubPage>
