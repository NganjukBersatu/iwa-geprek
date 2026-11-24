<script lang="ts">
	import { goto } from '$app/navigation';
	import LoginScreen from '$lib/features/login/components/LoginScreen.svelte';
	import { LoginState } from '$lib/features/login/login.svelte';

	const login = new LoginState();

	async function submit(): Promise<void> {
		if (await login.submit()) await goto('/dashboard', { replaceState: true });
	}
</script>

<LoginScreen {login} onSubmit={() => void submit()} />
