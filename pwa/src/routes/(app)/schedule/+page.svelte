<script lang="ts">
	import { goto } from '$app/navigation';
	import { current } from '$lib/auth/current.svelte';
	import ScheduleView from '$lib/features/schedule/components/ScheduleView.svelte';

	function expired(): void {
		current.signOut();
		void goto('/login', { replaceState: true });
	}
</script>

<ScheduleView onSessionExpired={expired} />
