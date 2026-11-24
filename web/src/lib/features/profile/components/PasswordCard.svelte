<script lang="ts">
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import type { ProfileState } from '../profile.svelte';
	import { profileText } from '$lib/text/profile';
	import { format } from '$lib/text/format';
	import { MIN_PASSWORD_LENGTH } from '$lib/auth/password-rules';

	let { profile }: { profile: ProfileState } = $props();

	let current = $state('');
	let next = $state('');
	let again = $state('');
	let problem = $state('');
	const errors = new FieldErrors({ current_password: profileText.currentPassword, new_password: profileText.newPassword, confirmation: profileText.confirmPassword }, () => profile.passwordFieldErrors);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(profile.passwordFieldErrors).length > 0) void focusRefused();
	});

	async function submit(): Promise<void> {
		problem = '';
		const found: Record<string, string> = {};
		if (!current) found.current_password = profileText.currentPasswordRequired;
		if (next.length < MIN_PASSWORD_LENGTH) found.new_password = format(profileText.passwordMinimum, { count: MIN_PASSWORD_LENGTH });
		else if (next !== again) found.confirmation = profileText.confirmMismatch;
		if (!errors.check(found)) return;
		const result = await profile.changePassword(current, next);
		if (result.ok) current = next = again = '';
		else problem = Object.keys(profile.passwordFieldErrors).length === 0 ? result.message : '';
	}
</script>

<Card>
	<CardHeader title={profileText.changePasswordTitle} description={profileText.passwordPrivacyNote} />
	<form class="mt-4 flex max-w-md flex-col gap-3" onsubmit={(event) => (event.preventDefault(), void submit())}>
		<TextField label={profileText.currentPassword} type="password" bind:value={current} autocomplete="off" required error={errors.get('current_password')} />
		<TextField label={profileText.newPassword} type="password" bind:value={next} autocomplete="new-password" required error={errors.get('new_password')} />
		<TextField label={profileText.confirmPassword} type="password" bind:value={again} autocomplete="new-password" required error={errors.get('confirmation')} />
		{#if problem}<Banner tone="danger" icon="alert-triangle">{problem}</Banner>{/if}
		<div><SaveButton type="submit" label={profileText.changePassword} busy={profile.changingPassword} /></div>
	</form>
</Card>
