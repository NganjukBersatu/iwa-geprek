<script lang="ts">
	import { termText } from '$lib/text/terms';
	import { PAGES, sopReadersPath } from '$lib/nav/pages';
	import { goto } from '$app/navigation';
	import { onDestroy, onMount } from 'svelte';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import DeleteButton from '$lib/components/button/DeleteButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import { api } from '$lib/api';
	import { userMessage } from '$lib/api/user-message';
	import { toast } from '$lib/components/feedback/toast.svelte';
	import BranchField from '$lib/components/form/BranchField.svelte';
	import CheckRow from '$lib/components/form/CheckRow.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import PageIntro from '$lib/components/header/PageIntro.svelte';
	import PhonePreview from '$lib/components/preview/PhonePreview.svelte';
	import Tabs from '$lib/components/tabs/Tabs.svelte';
	import { formatDateTime, formatTime } from '$lib/format/datetime';
	import type { SopDraftState } from '../sop-draft.svelte';
	import SlideFields from './SlideFields.svelte';
	import SlideStrip from './SlideStrip.svelte';
	import { actionText } from '$lib/text/actions';
	import { sopReadersText } from '$lib/text/sop-readers';
	import { sopText } from '$lib/text/sop';
	import { format } from '$lib/text/format';
	import RichText from '$lib/components/text/RichText.svelte';

	const LIST_PATH = PAGES.sop.path;
	const TABS = [
		{ key: 'tulis', label: sopText.write },
		{ key: 'pratinjau', label: sopText.preview }
	];

	let { draft }: { draft: SopDraftState } = $props();

	let tab = $state('tulis');
	let removing = $state(false);
	let removeBusy = $state(false);
	let removeError = $state('');
	const slide = $derived(draft.current);
	const autosaveText = $derived(
		draft.autosave === 'saving'
			? sopText.draftSaving
			: draft.autosave === 'saved' && draft.savedAt
				? format(sopText.draftSavedAt, { time: formatTime(draft.savedAt) })
				: draft.autosave === 'failed'
					? sopText.draftSaveFailed
					: ''
	);

	onMount(() => void draft.load());
	onDestroy(() => draft.dispose());

	$effect(() => {
		draft.state();
		draft.changed();
	});

	async function save(): Promise<void> {
		if (!(await draft.save())) return;
		toast.show(draft.id ? sopText.updated : sopText.added);
		await goto(LIST_PATH);
	}

	async function discard(): Promise<void> {
		if (await draft.discardDraft()) {
			toast.show(sopText.draftDiscarded);
			await goto(LIST_PATH);
		}
	}

	async function remove(): Promise<void> {
		if (!draft.id) return;
		removeBusy = true;
		removeError = '';
		try {
			await api.sop.remove(draft.id);
		} catch (error) {
			removeError = userMessage(error, sopText.removeFailed);
			return;
		} finally {
			removeBusy = false;
		}
		// Draf yang sudah tidak punya SOP tidak ikut memicu peringatan keluar halaman.
		draft.dispose();
		removing = false;
		toast.show(format(sopText.sopRemoved, { title: draft.title }));
		await goto(LIST_PATH);
	}

	function leave(event: BeforeUnloadEvent): void {
		if (draft.unsaved && !draft.saving) event.preventDefault();
	}
</script>

<svelte:window onbeforeunload={leave} />

<div class="flex flex-col gap-4 tablet:gap-6">
	<PageIntro
		title={draft.id ? sopText.editSop : sopText.addSop}
		description={sopText.editorDescription}
		items={draft.id
			? [{ label: PAGES.sop.label, href: LIST_PATH }, { label: draft.title || sopText.sop }, { label: actionText.edit }]
			: [{ label: PAGES.sop.label, href: LIST_PATH }, { label: sopText.addSop }]}
	>
		{#snippet actions()}
			{#if autosaveText}
				<span class="flex items-center gap-1.5 text-xs {draft.autosave === 'failed' ? 'text-danger-700' : 'text-slate-500'}" aria-live="polite">
					<i class="ti {draft.autosave === 'saving' ? 'ti-loader-2 animate-spin' : draft.autosave === 'failed' ? 'ti-cloud-off' : 'ti-cloud-check'}" aria-hidden="true"></i>{autosaveText}
				</span>
			{/if}
			{#if draft.id}
				<Button label={sopReadersText.readers} icon="users" href={sopReadersPath(draft.id)} />
				<DeleteButton label={sopText.removeSop} disabled={draft.saving || draft.loading} onclick={() => { removeError = ''; removing = true; }} />
			{:else if draft.hasDraft}
				<DeleteButton label={sopText.discardDraft} disabled={draft.saving || draft.loading} onclick={() => void discard()} />
			{/if}
			<CancelButton href={LIST_PATH} />
			<SaveButton label={sopText.saveSop} icon="device-floppy" busy={draft.saving} disabled={draft.loading || draft.pending !== null} onclick={() => void save()} />
		{/snippet}
	</PageIntro>

	{#if draft.error}
		<Banner tone="danger" icon="alert-triangle" title={sopText.openFailedTitle}>
			{draft.error}
			{#snippet action()}
				<Button label={actionText.retry} onclick={() => void draft.load()} />
			{/snippet}
		</Banner>
	{:else if draft.loading}
		<Notice loading text={sopText.loading} />
	{:else}
		{#if draft.pending}
			<Banner tone={draft.conflict ? 'warning' : 'info'} icon="file-pencil" title={sopText.unsavedDraftTitle}>
				{format(sopText.lastDraft, { time: formatDateTime(draft.pending.updated_at) })}
				{#if draft.conflict}{sopText.staleDraftWarning}{/if}
				{#snippet action()}
					<Button label={sopText.discardDraft} onclick={() => void draft.discardPending()} />
					<Button label={sopText.resumeDraft} icon="player-play" variant="primary" onclick={() => void draft.resume()} />
				{/snippet}
			</Banner>
		{/if}
		{#if draft.problem}
			<Banner tone="danger" icon="alert-triangle">{draft.problem}</Banner>
		{/if}

		<Card>
			<div class="grid items-end gap-3 tablet:grid-cols-[minmax(0,1fr)_14rem_auto]">
				<TextField label={sopText.sopTitle} bind:value={draft.title} maxlength={120} required placeholder={sopText.sopTitleExample} />
				<BranchField label={sopText.availableIn} bind:value={draft.outletId} everyLabel={draft.canChooseEveryBranch ? termText.allBranches : undefined} />
				<CheckRow label={sopText.shownToEmployees} hint={sopText.shownToEmployeesHint} checked={draft.active} onchange={() => (draft.active = !draft.active)} />
			</div>
		</Card>

		<Card flush>
			<Tabs tabs={TABS} bind:value={tab} label={sopText.editorView}>
				{#snippet actions()}
					{#if tab === 'tulis'}
						<Button label={sopText.perSlide} icon="square" compact active={draft.mode === 'one'} onclick={() => (draft.mode = 'one')} />
						<Button label={sopText.allSlides} icon="layout-list" compact active={draft.mode === 'all'} onclick={() => (draft.mode = 'all')} />
					{/if}
				{/snippet}
			</Tabs>

			{#if tab === 'pratinjau'}
				<div class="p-4 tablet:p-6">
					<PhonePreview title={draft.title} pages={draft.slides} bind:index={draft.selected} />
				</div>
			{:else if draft.mode === 'one'}
				<SlideStrip {draft} />
				{#if slide}
					{#key slide.uid}
						<SlideFields {slide} onupload={draft.uploadMedia} />
					{/key}
				{/if}
			{:else}
				<div class="flex flex-col divide-y divide-slate-100">
					{#each draft.slides as item, index (item.uid)}
						<section class="flex flex-col" aria-label={format(sopText.slideNumber, { number: index + 1 })}>
							<div class="flex items-center justify-between gap-2 px-4 pt-4 tablet:px-5">
								<p class="text-sm font-semibold text-slate-800">{format(sopText.slideNumber, { number: index + 1 })}</p>
								<div class="flex items-center gap-0.5">
									<Button label={sopText.moveUp} icon="arrow-up" variant="tertiary" small compact disabled={index === 0} onclick={() => draft.move(index, -1)} />
									<Button label={sopText.moveDown} icon="arrow-down" variant="tertiary" small compact disabled={index === draft.slides.length - 1} onclick={() => draft.move(index, 1)} />
									<DeleteButton small disabled={draft.slides.length <= 1} onclick={() => draft.remove(index)} />
								</div>
							</div>
							<SlideFields slide={item} onupload={draft.uploadMedia} />
						</section>
					{/each}
					<div class="p-4 tablet:px-5">
						<Button label={sopText.addSlide} icon="plus" onclick={() => draft.add()} />
					</div>
				</div>
			{/if}
		</Card>
	{/if}
</div>

<ConfirmDialog open={removing} title={sopText.removeTitle} confirmLabel="Hapus" danger busy={removeBusy} error={removeError} onconfirm={() => void remove()} oncancel={() => (removing = false)}>
	<RichText template={sopText.sopRemoveNote} values={{ title: draft.title }} />
</ConfirmDialog>
