<script lang="ts">
	import { goto } from '$app/navigation';
	import { current } from '$lib/auth/current.svelte';
	import AttendanceView from '$lib/features/attendance/components/AttendanceView.svelte';

	function expired(): void {
		current.signOut();
		void goto('/login', { replaceState: true });
	}
</script>

<AttendanceView onSessionExpired={expired} />
