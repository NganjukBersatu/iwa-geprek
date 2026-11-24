<script lang="ts">
	import { page } from '$app/state';
	import LoginView from '$lib/features/login/components/LoginView.svelte';
	import { LoginState } from '$lib/features/login/login.svelte';
	import { authText } from '$lib/text/auth';

	const login = new LoginState(page.url.searchParams.get('dari'));
</script>

<svelte:head><title>{authText.login.pageTitle}</title></svelte:head>

<LoginView {login} />
