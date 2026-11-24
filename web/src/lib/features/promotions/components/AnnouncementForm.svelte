<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import { PAGES, announcementPath } from '$lib/nav/pages';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import type { Announcement, AnnouncementCreate, AnnouncementUpdate } from '$lib/api/types';
	import Banner from '$lib/components/card/Banner.svelte';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import FormSection from '$lib/components/form/FormSection.svelte';
	import CheckRow from '$lib/components/form/CheckRow.svelte';
	import PhotoField from '$lib/components/form/PhotoField.svelte';
	import ScopeField from '$lib/components/form/ScopeField.svelte';
	import { branches } from '$lib/stores/branch';
	import TextArea from '$lib/components/form/TextArea.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import { todayIso } from '$lib/date/range';
	import { untrack } from 'svelte';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { promotionText } from '$lib/text/promotions';
	import { format } from '$lib/text/format';

	let {
		announcement,
		busy,
		error,
		fieldErrors = {},
		onsave,
		onclose
	}: {
		announcement: Announcement | null;
		busy: boolean;
		error: string;
		/** What the server refused, by field name, shown under the field itself. */
		fieldErrors?: Record<string, string>;
		onsave: (body: AnnouncementCreate | AnnouncementUpdate, image: File | null) => void;
		onclose: () => void;
	} = $props();

	const current = untrack(() => announcement);
	const trail = [
		{ label: PAGES.promotions.label, href: PAGES.promotions.path },
		...(current ? [{ label: current.title, href: announcementPath(current.id) }, { label: actionText.edit }] : [{ label: promotionText.addAnnouncement }])
	];
	const initialLink = current?.image_is_link ? (current.image_url ?? '') : '';

	let title = $state(current?.title ?? '');
	let scope = $state(current?.outlet_id ?? '');
	let description = $state(current?.description ?? '');
	let link = $state(initialLink);
	let image = $state<File | null>(null);
	let startsOn = $state(current?.starts_on ?? todayIso());
	let endsOn = $state(current?.ends_on ?? todayIso());
	let active = $state(current?.is_active ?? true);
	const errors = new FieldErrors(
		{ title: promotionText.title, starts_on: promotionText.startDate, ends_on: promotionText.endDate, description: termText.description, image_link: promotionText.imageLink },
		() => fieldErrors
	);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(fieldErrors).length > 0) void focusRefused();
	});

	function submit(): void {
		const found: Record<string, string> = {};
		const typedLink = link.trim();
		if (!title.trim()) found.title = promotionText.titleRequired;
		if (!startsOn) found.starts_on = promotionText.announcementStartRequired;
		if (!endsOn) found.ends_on = promotionText.announcementEndRequired;
		else if (startsOn && endsOn < startsOn) found.ends_on = promotionText.endBeforeStart;
		if (!description.trim()) found.description = promotionText.announcementDescriptionRequired;
		if (typedLink && !/^https?:\/\//i.test(typedLink)) found.image_link = promotionText.imageLinkInvalid;
		if (!errors.check(found)) return;
		const body: AnnouncementCreate | AnnouncementUpdate = { title: title.trim(), description: description.trim(), starts_on: startsOn, ends_on: endsOn, is_active: active, outlet_id: scope || null };
		// The link is sent only when it changed, so an uploaded picture is not dropped by an unrelated edit.
		if (!current || typedLink !== initialLink) body.image_link = typedLink || null;
		onsave(body, image);
	}
</script>

<FormPage title={current ? format(controlText.editName, { name: current.title }) : promotionText.addAnnouncement} description={promotionText.announcementFormDescription} stacked {trail} {busy} {onclose}>
	<FormSection icon="speakerphone" title={promotionText.announcement} description={promotionText.announcementSectionDescription}>
		<TextField label={promotionText.title} bind:value={title} maxlength={255} required error={errors.get('title')} />
		<ScopeField bind:value={scope} outlets={$branches} />
		<div class="grid gap-3 tablet:grid-cols-2">
			<TextField label={promotionText.startDate} type="date" bind:value={startsOn} required error={errors.get('starts_on')} />
			<TextField label={promotionText.endDate} type="date" bind:value={endsOn} required error={errors.get('ends_on')} />
		</div>
		<TextArea label={termText.description} bind:value={description} maxlength={2000} rows={4} required error={errors.get('description')} />
		<CheckRow label={termText.active} checked={active} onchange={() => (active = !active)} />
	</FormSection>
	<FormSection icon="photo" title={promotionText.image} description={promotionText.imageSectionDescription}>
		<PhotoField label={promotionText.image} current={current && !current.image_is_link ? current.image_url : null} alt={format(promotionText.imageOf, { name: current?.title ?? 'promosi' })} bind:file={image} disabled={busy} />
		<TextField label={promotionText.orImageLink} bind:value={link} maxlength={1000} hint={promotionText.uploadReplacesLink} error={errors.get('image_link')} />
	</FormSection>
	{#if error && errors.count === 0}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
	{/if}

	{#snippet footer()}
		<SaveButton busy={busy} onclick={submit} />
		<CancelButton disabled={busy} onclick={onclose} />
	{/snippet}
</FormPage>
