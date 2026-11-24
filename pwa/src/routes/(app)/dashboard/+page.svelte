<script lang="ts">
	import { goto } from '$app/navigation';
	import { current } from '$lib/auth/current.svelte';
	import DashboardView from '$lib/features/dashboard/components/DashboardView.svelte';

	function expired(): void {
		current.signOut();
		void goto('/login', { replaceState: true });
	}
</script>

<DashboardView onOpenAttendance={() => void goto('/presence?from=dashboard')} onSessionExpired={expired} />
