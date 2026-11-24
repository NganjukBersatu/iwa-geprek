<script lang="ts">
	import { goto } from '$app/navigation';
	import { current } from '$lib/auth/current.svelte';
	import ProfileView from '$lib/features/profile/components/ProfileView.svelte';

	function signOut(): void {
		current.signOut();
		void goto('/login', { replaceState: true });
	}

	async function logOut(): Promise<boolean> {
		if (!(await current.logOut())) return false;
		void goto('/login', { replaceState: true });
		return true;
	}
</script>

<ProfileView onLogout={logOut} onSessionExpired={signOut} />
