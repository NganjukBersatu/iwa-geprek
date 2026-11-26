<script lang="ts">
	import { onMount } from 'svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import DeleteButton from '$lib/components/button/DeleteButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import CheckRow from '$lib/components/form/CheckRow.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import PageIntro from '$lib/components/header/PageIntro.svelte';
	import SkeletonPage from '$lib/components/skeleton/SkeletonPage.svelte';
	import { PAGES } from '$lib/nav/pages';
	import { KIND_HINT, KIND_LABEL } from '../labels';
	import type { StationEditState } from '../station-edit.svelte';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { stationText } from '$lib/text/stations';
	import { format } from '$lib/text/format';

	let { edit }: { edit: StationEditState } = $props();

	onMount(() => void edit.load());

	const MAX_NAME = 40;
	const kindOptions = Object.entries(KIND_LABEL).map(([value, label]) => ({ value, label }));
	// Stasiun Kasir dipegang setiap perangkat Mode Kasir; server menolak menghapus atau mengganti jenisnya.
	const cashierLocked = $derived(edit.station?.kind === 'handover');

	const branchesDescription = $derived(
		[stationText.perBranchEditDescription, edit.kind === 'deliver' ? stationText.perBranchTargetNote : '', edit.kind !== 'handover' ? stationText.perBranchRolesNote : '']
			.filter(Boolean)
			.join(' ')
	);
</script>

<div class="flex flex-col gap-4 tablet:gap-6">
	<PageIntro
		title={edit.creating ? stationText.newStation : (edit.station?.name ?? termText.station)}
		description={stationText.defaultsDescription}
		items={[{ label: termText.station }, { label: PAGES.stationSetup.label, href: PAGES.stationSetup.path }, { label: edit.creating ? stationText.newStation : (edit.station?.name ?? termText.station) }]}
	>
		{#snippet actions()}
			{#if !edit.creating && edit.station && !cashierLocked}
				<DeleteButton disabled={edit.saving} onclick={() => (edit.confirmingDelete = true)} />
			{/if}
		{/snippet}
	</PageIntro>

	{#if edit.error}
		<Banner tone="danger" icon="alert-triangle" title={stationText.stationLoadFailedTitle}>
			{edit.error}
			{#snippet action()}
				<Button label={actionText.retry} onclick={() => void edit.load()} />
			{/snippet}
		</Banner>
	{:else if edit.loading}
		<SkeletonPage label={stationText.stationLoading} />
	{:else}
		{#if edit.saveError}
			<Banner tone="danger" icon="alert-triangle">{edit.saveError}</Banner>
		{/if}

		<div class="grid grid-cols-1 gap-4 laptop:grid-cols-2 tablet:gap-6">
			<Card>
				<CardHeader title={termText.station} description={KIND_HINT[edit.kind]} icon="tools-kitchen-2" />
				<div class="mt-4 flex flex-col gap-3">
					<TextField label={termText.name} bind:value={edit.name} maxlength={MAX_NAME} required />
					{#if cashierLocked}
						<TextField label={termText.kind} value={KIND_LABEL.handover} readonly hint={stationText.cashierKindLocked} />
					{:else}
						<SelectField label={termText.kind} options={kindOptions} bind:value={edit.kind} />
					{/if}
					{#if edit.kind === 'deliver'}
						<div class="grid grid-cols-2 gap-3">
							<TextField label={stationText.targetHours} inputmode="numeric" bind:value={edit.target.hours} maxlength={2} />
							<TextField label={stationText.targetMinutes} inputmode="numeric" bind:value={edit.target.minutes} maxlength={2} />
						</div>
					{/if}
				</div>
				<div class="mt-4 flex justify-end">
					<SaveButton busy={edit.saving} onclick={() => void edit.save()} />
				</div>
			</Card>

			{#if !edit.creating && edit.kind !== 'handover' && edit.roles.length > 0}
				<Card flush>
					<CardHeader divided title={stationText.defaultRoles} description={stationText.defaultRolesDescription} icon="users" />
					<div class="grid grid-cols-1 gap-x-4 px-3 py-2 tablet:grid-cols-2">
						{#each edit.roles as role (role.id)}
							<CheckRow label={role.name} checked={edit.defaultRoleIds.includes(role.id)} onchange={() => edit.toggleDefaultRole(role.id)} />
						{/each}
					</div>
					<div class="flex items-center justify-end border-t border-slate-100 p-4">
						<SaveButton label={stationText.saveDefaultRoles} busy={edit.saving} onclick={() => void edit.saveRoles()} />
					</div>
				</Card>
			{/if}

			{#if !edit.creating && edit.branches.length > 0}
				<Card flush class="laptop:col-span-2">
					<CardHeader divided title={stationText.perBranch} description={branchesDescription} icon="building-store" />
					<div class="flex flex-col divide-y divide-slate-100">
						{#each edit.branches as branch (branch.outletId)}
							<div class="flex flex-col gap-2 px-4 py-3">
								<div class="flex flex-wrap items-center justify-between gap-2">
									<span class="text-sm font-semibold text-slate-800">{branch.name}</span>
									<span class="flex flex-wrap items-center gap-2">
										<Badge tone={branch.used ? 'success' : 'neutral'}>{branch.used ? stationText.branchActive : stationText.branchInactive}</Badge>
										{#if edit.branches.length > 1}
											<Button label={stationText.copyToOthers} icon="copy" variant="tertiary" disabled={edit.saving} onclick={() => (edit.copyFrom = branch)} />
										{/if}
									</span>
								</div>
								<div class="flex flex-wrap items-end gap-3">
									<div class="w-40">
										<TextField label={stationText.reminderSeconds} inputmode="numeric" bind:value={branch.reminder} maxlength={3} />
									</div>
									{#if edit.kind === 'deliver'}
										<div class="grid w-48 grid-cols-2 gap-2">
											<TextField label={stationText.hours} inputmode="numeric" bind:value={branch.target.hours} maxlength={2} />
											<TextField label={stationText.minutes} inputmode="numeric" bind:value={branch.target.minutes} maxlength={2} />
										</div>
									{/if}
								</div>
								{#if edit.kind !== 'handover' && edit.roles.length > 0}
									<details class="text-xs">
										<summary class="cursor-pointer font-semibold text-slate-600">
											{format(stationText.branchRoles, { summary: branch.roleIds.length > 0 ? format(stationText.ownRoles, { count: branch.roleIds.length }) : stationText.followDefaultRoles })}
										</summary>
										<div class="mt-1 grid grid-cols-1 gap-x-4 tablet:grid-cols-2">
											{#each edit.roles as role (role.id)}
												<CheckRow label={role.name} checked={branch.roleIds.includes(role.id)} onchange={() => edit.toggleRole(branch, role.id)} />
											{/each}
										</div>
									</details>
								{/if}
							</div>
						{/each}
					</div>
					<div class="flex flex-col gap-3 border-t border-slate-100 p-4">
						{#if edit.branchError}<Banner tone="danger" icon="alert-triangle">{edit.branchError}</Banner>{/if}
						<div class="flex items-center justify-between gap-3">
							<span class="text-xs text-slate-500">{format(stationText.activeInBranchesCount, { active: edit.activeCount, total: edit.branches.length })}</span>
							<SaveButton busy={edit.saving} onclick={() => void edit.saveBranches()} />
						</div>
					</div>
				</Card>
			{/if}
		</div>
	{/if}
</div>

<ConfirmDialog
	open={edit.confirmingDelete}
	title={stationText.removeTitle}
	confirmLabel={stationText.removeConfirm}
	danger
	busy={edit.saving}
	error={edit.saveError}
	onconfirm={() => void edit.remove()}
	oncancel={() => (edit.confirmingDelete = false)}
>
	{format(stationText.stationRemoveNote, { name: edit.station?.name ?? '' })}
</ConfirmDialog>

<ConfirmDialog
	open={edit.copyFrom !== null}
	title={format(stationText.copyTitle, { name: edit.copyFrom?.name ?? '' })}
	confirmLabel={stationText.copyConfirm}
	busy={edit.saving}
	onconfirm={() => void edit.copyToOthers()}
	oncancel={() => (edit.copyFrom = null)}
>
	{format(stationText.copyNote, { name: edit.copyFrom?.name ?? '', count: edit.branches.length - 1 })}
</ConfirmDialog>
