<script lang="ts">
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import PersonalFields from '$lib/components/form/PersonalFields.svelte';
	import { PERSONAL_LABELS, personalBody, personalFrom } from '$lib/components/form/personal';
	import TextField from '$lib/components/form/TextField.svelte';
	import { unsavedChanges } from '$lib/components/form/unsaved-changes.svelte';
	import { formatDate } from '$lib/date/range';
	import SkeletonPage from '$lib/components/skeleton/SkeletonPage.svelte';
	import { EMPTY_VALUE } from '$lib/format/currency';
	import { untrack } from 'svelte';
	import type { ProfileState } from '../profile.svelte';
	import Reveal from '$lib/components/motion/Reveal.svelte';
	import PasswordCard from './PasswordCard.svelte';
	import ProfilePhoto from './ProfilePhoto.svelte';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { profileText } from '$lib/text/profile';

	let { profile }: { profile: ProfileState } = $props();

	const person = $derived(profile.profile);
	const identity = $derived(
		person
			? [
					{ label: profileText.username, value: person.username },
					{ label: termText.role, value: person.role_name },
					{ label: termText.branch, value: person.outlet_name ?? termText.allBranches },
					{ label: profileText.joinedDate, value: person.joined_date ? formatDate(person.joined_date) : EMPTY_VALUE }
				]
			: []
	);

	let name = $state('');
	let personal = $state(personalFrom(null));
	let problem = $state('');
	const errors = new FieldErrors({ name: profileText.displayName, ...PERSONAL_LABELS }, () => profile.fieldErrors);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(profile.fieldErrors).length > 0) void focusRefused();
	});

	// The form starts from what the server holds, and again after each save.
	$effect(() => {
		void profile.revision;
		const held = untrack(() => profile.profile);
		name = held?.name ?? '';
		personal = personalFrom(held);
	});

	async function submit(): Promise<void> {
		problem = '';
		if (!errors.check(name.trim() ? {} : { name: profileText.displayNameRequired })) return;
		unsavedChanges.clear();
		const result = await profile.save({ name: name.trim(), ...personalBody(personal) });
		problem = errors.count === 0 ? result.message : '';
	}
</script>

{#if profile.loading && !person}
	<SkeletonPage stats={0} label={profileText.loading} />
{:else if !person}
	<Card>
		<Notice text={profile.error || profileText.loadFailed} />
		<div class="flex justify-center pb-2"><Button label={actionText.retry} icon="refresh" onclick={() => void profile.load()} /></div>
	</Card>
{:else}
	<Reveal>
		<Card>
			<CardHeader title={termText.account} />
			<div class="mt-4"><ProfilePhoto {profile} /></div>

			<div class="mt-6"><FigureList title={profileText.identity} figures={identity} /></div>

			<form class="mt-6 flex flex-col gap-4 border-t border-slate-100 pt-5" use:unsavedChanges.watch onsubmit={(event) => (event.preventDefault(), void submit())}>
				<div class="max-w-md"><TextField label={profileText.displayName} bind:value={name} maxlength={255} required error={errors.get('name')} /></div>
				<PersonalFields bind:data={personal} error={(field) => errors.get(field)} />
				{#if problem}<Banner tone="danger" icon="alert-triangle">{problem}</Banner>{/if}
				<div><SaveButton type="submit" label={actionText.save} busy={profile.saving} /></div>
			</form>
		</Card>

		<PasswordCard {profile} />
	</Reveal>
{/if}
