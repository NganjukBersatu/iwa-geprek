<script lang="ts">
	import DeleteButton from '$lib/components/button/DeleteButton.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import PhotoField from '$lib/components/form/PhotoField.svelte';
	import type { ProfileState } from '../profile.svelte';
	import { profileText } from '$lib/text/profile';

	let { profile }: { profile: ProfileState } = $props();

	const person = $derived(profile.profile);
	let problem = $state('');
</script>

<div class="flex flex-col gap-2">
	<PhotoField
		label={profileText.photo}
		current={person?.photo_url ?? null}
		alt={person?.name || person?.username || ''}
		disabled={profile.photoBusy}
		onpick={async (file) => (problem = await profile.setPhoto(file))}
	>
		{#snippet actions()}
			{#if person?.photo_url}
				<DeleteButton label={profileText.removePhoto} disabled={profile.photoBusy} onclick={async () => (problem = await profile.removePhoto())} />
			{/if}
		{/snippet}
	</PhotoField>
	{#if problem}<Banner tone="danger" icon="alert-triangle">{problem}</Banner>{/if}
</div>
