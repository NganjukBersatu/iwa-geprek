<script lang="ts">
	import { onMount } from 'svelte';
	import PageHeader from '$lib/components/header/PageHeader.svelte';
	import ProfileView from '$lib/features/profile/components/ProfileView.svelte';
	import { ProfileState } from '$lib/features/profile/profile.svelte';
	import { pageText } from '$lib/text/pages';

	const profile = new ProfileState();

	onMount(() => void profile.load());
</script>

<div class="flex flex-col gap-4 tablet:gap-6">
	<PageHeader title={pageText.profileTitle} description={pageText.profileDescription} />
	<ProfileView {profile} />
</div>
