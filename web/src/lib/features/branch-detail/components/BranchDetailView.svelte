<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { onMount, type Snippet } from 'svelte';
	import type { BranchUpdate } from '$lib/api/types';
	import { access } from '$lib/auth/access.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import PageIntro from '$lib/components/header/PageIntro.svelte';
	import Tabs from '$lib/components/tabs/Tabs.svelte';
	import { live } from '$lib/live/live';
	import { enter } from '$lib/motion/transitions';
	import { BRANCH_TABS, PAGES, branchPath, type BranchTab } from '$lib/nav/pages';
	import { memoryKey, remember } from '$lib/stores/memory';
	import { branchDetailText as text } from '$lib/text/branch-detail';
	import { actionText } from '$lib/text/actions';
	import { format } from '$lib/text/format';
	import { editAddress } from '../../record-detail/edit-address.svelte';
	import BranchForm from '../../branches/components/BranchForm.svelte';
	import type { BranchDetailState } from '../branch-detail.svelte';
	import { untrack } from 'svelte';

	let {
		detail,
		tabs = [],
		children
	}: {
		detail: BranchDetailState;
		/** Hanya bagian yang boleh dibuka peran ini; yang pertama dibuka bila alamat tidak menyebut tab. */
		tabs?: { key: BranchTab; label: string }[];
		children?: Snippet<[BranchTab]>;
	} = $props();

	const branch = $derived(detail.branch);
	const address = editAddress();
	const canRemove = $derived(access.allows('remove_branches'));
	const removalStarted = $derived(branch?.removal_started_at != null);
	const removalPercent = $derived(detail.removal ? Math.round((detail.removal.finished_parts / Math.max(detail.removal.total_parts, 1)) * 100) : 0);
	const tab = $derived(tabs.find((item) => item.key === page.url.searchParams.get('tab'))?.key ?? tabs[0]?.key);

	// Membuka detail sebuah cabang sama dengan memilih cabang itu, jadi setiap bagian di bawahnya dan halaman lain ikut cabang ini.
	remember(memoryKey.filter('cabang'), untrack(() => detail.id));

	async function saveAndReturn(body: BranchUpdate): Promise<void> {
		if (await detail.save(body)) void goto(address.recordPath);
	}

	function pick(key: string): void {
		const next = tabs.find((item) => item.key === key);
		if (next) void goto(branchPath(detail.id, next.key), { replaceState: true, noScroll: true, keepFocus: true });
	}

	$effect(() => {
		if (detail.removed) void goto(PAGES.branches.path, { replaceState: true });
	});

	onMount(() => {
		void detail.load();
		return live.on(['outlets'], () => void detail.refresh());
	});
</script>

{#if detail.error}
	<Banner tone="danger" icon="alert-triangle" title={text.loadFailed}>
		{detail.error}
		{#snippet action()}
			<Button label={actionText.retry} onclick={() => void detail.load()} />
		{/snippet}
	</Banner>
{:else if branch && address.editing}
	<BranchForm {branch} busy={detail.busy} error={detail.actionError} fieldErrors={detail.fieldErrors} onsave={(body) => void saveAndReturn(body as BranchUpdate)} onclose={() => void goto(address.recordPath)} />
{:else if branch}
	<div class="flex flex-col gap-4 tablet:gap-6">
		<PageIntro
			title={branch.name}
			description={[branch.code, branch.receipt_number ? format(text.numberLabel, { number: branch.receipt_number }) : ''].filter(Boolean).join(' · ') || text.noCode}
			items={[{ label: PAGES.branches.label, href: PAGES.branches.path }, { label: branch.name }]}
		>
			{#snippet badge()}
				<Badge tone={branch.is_active ? 'success' : 'neutral'}>{branch.is_active ? text.open : text.closed}</Badge>
			{/snippet}
			{#snippet actions()}
				{#if !removalStarted}
					<Button label={actionText.edit} icon="pencil" variant="primary" disabled={detail.busy} onclick={() => void goto(address.editPath)} />
					<Button
						label={branch.is_active ? text.close : text.reopen}
						icon={branch.is_active ? 'building-off' : 'building-store'}
						variant={branch.is_active ? 'dangerOutline' : 'tertiary'}
						disabled={detail.busy}
						onclick={() => detail.askToggle()}
					/>
				{/if}
				{#if canRemove && !branch.is_active}
					<Button label={text.removePermanently} icon="trash" variant="danger" disabled={detail.busy} onclick={() => detail.askRemove()} />
				{/if}
			{/snippet}
		</PageIntro>

		{#if removalStarted}
			<Banner tone="danger" icon="trash" title={text.removalUnfinishedTitle}>
				{text.removalUnfinishedBody}
				{#snippet action()}
					{#if canRemove}
						<Button label={text.continueRemoval} variant="danger" onclick={() => detail.askRemove()} />
					{/if}
				{/snippet}
			</Banner>
		{/if}

		{#if detail.actionError && !detail.toggling && !detail.removing}
			<Banner tone="danger" icon="alert-triangle">{detail.actionError}</Banner>
		{/if}

		{#if tab && children}
			<Tabs {tabs} label={text.tabsLabel} variant="pill" bind:value={() => tab, pick} />
			{#key tab}
				<div class="flex flex-col gap-4 tablet:gap-6" in:enter>
					{@render children(tab)}
				</div>
			{/key}
		{/if}
	</div>

	<ConfirmDialog
		open={detail.toggling}
		title={branch.is_active ? text.closeTitle : text.reopenTitle}
		confirmLabel={branch.is_active ? text.close : text.reopen}
		danger={branch.is_active}
		busy={detail.busy}
		error={detail.actionError}
		onconfirm={() => void detail.confirmToggle()}
		oncancel={() => detail.closeDialogs()}
	>
		<strong class="text-slate-800">{branch.name}</strong>
		{branch.is_active ? text.closeNote : text.reopenNote}
	</ConfirmDialog>

	<ConfirmDialog
		open={detail.removing}
		title={text.removeTitle}
		confirmLabel={text.removeConfirm}
		danger
		busy={detail.busy}
		error={detail.actionError}
		typeToConfirm={branch.name}
		onconfirm={() => void detail.confirmRemove()}
		oncancel={() => detail.closeDialogs()}
	>
		<p><strong class="text-slate-800">{branch.name}</strong> {text.removeIntro} <strong class="text-slate-800">{text.removeIrreversible}</strong>:</p>
		<ul class="mt-2 list-disc pl-5">
			{#each text.removeList as line (line)}
				<li>{line}</li>
			{/each}
		</ul>
		<p class="mt-2">{text.removeEffects}</p>
		{#if detail.busy && detail.removal}
			<p class="mt-2 font-medium text-slate-800" role="status">{format(text.removeProgress, { percent: removalPercent, done: detail.removal.finished_parts, total: detail.removal.total_parts })}</p>
		{:else if detail.busy}
			<p class="mt-2 font-medium text-slate-800" role="status">{text.removing}</p>
		{/if}
	</ConfirmDialog>
{:else}
	<Notice loading text={text.loading} />
{/if}
