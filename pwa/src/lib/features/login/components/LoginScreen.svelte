<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import PrimaryButton from '$lib/components/button/PrimaryButton.svelte';
	import PasswordField from '$lib/components/field/PasswordField.svelte';
	import TextField from '$lib/components/field/TextField.svelte';
	import InlineMessage from '$lib/components/feedback/InlineMessage.svelte';
	import AuthCard from '$lib/components/layout/AuthCard.svelte';
	import AppText from '$lib/components/text/AppText.svelte';
	import { t } from '$lib/text/t';
	import type { LoginState } from '../login.svelte';

	let { login, onSubmit }: { login: LoginState; onSubmit: () => void } = $props();

	const hasError = $derived(login.error !== null);
</script>

<AuthCard brandImage="/brand-logo.png" brandDescription={t('shell_logo_description')}>
	{#snippet content(wide)}
		<AppText role={wide ? 'display' : 'headline'} color="background">{t('web_login_title')}</AppText>
		<div class="h-1"></div>
		<AppText role="body" color="background">{t('web_login_subtitle')}</AppText>
		<div use:dynamicStyle={{ height: `${wide ? 48 : 32}px` }}></div>

		<TextField
			bind:value={login.username}
			label={t('login_username_label')}
			placeholder={t('login_username_placeholder')}
			enabled={!login.submitting}
			isError={hasError}
			labelColor="on-primary"
			focusColor="accent"
			autocomplete="username"
			enterkeyhint="next"
			oninput={login.clearError.bind(login)}
		/>
		<div class="h-4"></div>
		<PasswordField
			bind:value={login.password}
			label={t('login_password_label')}
			placeholder={t('login_password_placeholder')}
			showDescription={t('password_show')}
			hideDescription={t('password_hide')}
			enabled={!login.submitting}
			isError={hasError}
			labelColor="on-primary"
			focusColor="accent"
			autocomplete="current-password"
			oninput={login.clearError.bind(login)}
			onenter={() => login.canSubmit && onSubmit()}
		/>
		{#if login.error}
			<div class="mt-3"><InlineMessage text={login.error} /></div>
		{/if}
		<div use:dynamicStyle={{ height: `${wide ? 32 : 24}px` }}></div>
		<PrimaryButton
			text={login.submitting ? t('login_submitting') : t('login_submit')}
			onclick={onSubmit}
			enabled={login.canSubmit}
			container="surface-accent"
			content="content"
			loading={login.submitting}
		/>
		<div class="h-6"></div>
		<AppText role="caption" color="background" align="center">{t('web_login_forgot_password')}</AppText>
	{/snippet}
</AuthCard>
