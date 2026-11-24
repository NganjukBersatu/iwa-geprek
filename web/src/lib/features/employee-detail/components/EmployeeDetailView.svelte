<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import type { EmployeeUpdate } from '$lib/api/types';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import PageIntro from '$lib/components/header/PageIntro.svelte';
	import { formatDate } from '$lib/date/range';
	import { EMPTY_VALUE } from '$lib/format/currency';
	import { live } from '$lib/live/live';
	import { PAGES } from '$lib/nav/pages';
	import { employeeDetailText as text } from '$lib/text/employee-detail';
	import { assignableRoles } from '../../roles/assignable';
	import { editAddress } from '../../record-detail/edit-address.svelte';
	import EmployeeForm from '../../employees/components/EmployeeForm.svelte';
	import type { EmployeeDetailState } from '../employee-detail.svelte';
	import { actionText } from '$lib/text/actions';
	import { format } from '$lib/text/format';

	let { detail }: { detail: EmployeeDetailState } = $props();

	const employee = $derived(detail.employee);
	const gender = (value: string | null) => (value === 'L' ? text.male : value === 'P' ? text.female : EMPTY_VALUE);
	const date = (value: string | null) => (value ? formatDate(value) : EMPTY_VALUE);
	const plain = (value: string | null) => value || EMPTY_VALUE;

	const address = editAddress();

	async function saveAndReturn(body: EmployeeUpdate): Promise<void> {
		if (await detail.save(body)) void goto(address.recordPath);
	}

	onMount(() => {
		void detail.load();
		return live.on(['users', 'roles'], () => void detail.refresh());
	});

	async function remove(): Promise<void> {
		if (await detail.remove()) void goto(PAGES.user.path);
	}
</script>

{#if detail.error}
	<Banner tone="danger" icon="alert-triangle" title={text.loadFailed}>
		{detail.error}
		{#snippet action()}
			<Button label={actionText.retry} onclick={() => void detail.load()} />
		{/snippet}
	</Banner>
{:else if employee && address.editing && !employee.locked}
	<EmployeeForm
		{employee}
		roles={assignableRoles(detail.roles)}
		outlets={detail.outlets}
		busy={detail.busy}
		error={detail.actionError}
		fieldErrors={detail.fieldErrors}
		onsave={(body) => void saveAndReturn(body as EmployeeUpdate)}
		onclose={() => void goto(address.recordPath)}
	/>
{:else if employee}
	<div class="flex flex-col gap-4 tablet:gap-6">
		<PageIntro
			title={employee.name || employee.username}
			description="{employee.role_name} · {detail.branchName(employee.outlet_id)}"
			items={[{ label: PAGES.user.label, href: PAGES.user.path }, { label: employee.name || employee.username }]}
		>
			{#snippet badge()}
				<Badge tone={employee.is_active ? 'success' : 'neutral'}>{employee.is_active ? text.active : text.inactive}</Badge>
			{/snippet}
			{#snippet actions()}
				<Button label={actionText.edit} icon="pencil" variant="primary" disabled={detail.busy || employee.locked} hint={text.locked} onclick={() => void goto(address.editPath)} />
				<Button label={text.remove} icon="trash" variant="danger" disabled={detail.busy || employee.locked} hint={text.locked} onclick={() => detail.askRemove()} />
			{/snippet}
		</PageIntro>

		{#if detail.actionError && !detail.removing}
			<Banner tone="danger" icon="alert-triangle">{detail.actionError}</Banner>
		{/if}

		<Card flush class="grid laptop:grid-cols-3">
			<div class="flex flex-col gap-4 border-b border-slate-100 p-4 tablet:p-5 laptop:border-b-0 laptop:border-r">
				<div class="flex items-center gap-3">
					{#if employee.photo_url}
						<img src={employee.photo_url} alt={format(controlText.photoOf, { name: employee.name || employee.username })} class="size-12 shrink-0 rounded-full border border-brand-line object-cover" />
					{:else}
						<span class="flex size-12 shrink-0 items-center justify-center rounded-full bg-brand-soft text-lg font-semibold text-brand-deep" aria-hidden="true">{(employee.name || employee.username).charAt(0).toUpperCase()}</span>
					{/if}
					<div class="min-w-0">
						<p class="truncate text-sm font-semibold text-slate-800">{employee.role_name}</p>
						<p class="truncate text-xs text-slate-500">{detail.branchName(employee.outlet_id)}</p>
					</div>
				</div>
				<FigureList
					title={text.sections.account}
					figures={[
						{ label: text.labels.name, value: plain(employee.name) },
						{ label: text.labels.username, value: employee.username },
						{ label: text.labels.status, value: employee.is_active ? text.active : text.inactive },
						{ label: text.labels.joined, value: date(employee.joined_date) }
					]}
				/>
			</div>
			<div class="border-b border-slate-100 p-4 tablet:p-5 laptop:border-b-0 laptop:border-r">
				<FigureList
					title={text.sections.personal}
					figures={[
						{ label: text.labels.phone, value: plain(employee.phone) },
						{ label: text.labels.email, value: plain(employee.email) },
						{ label: text.labels.birthDate, value: date(employee.birth_date) },
						{ label: text.labels.gender, value: gender(employee.gender) },
						{ label: text.labels.address, value: plain(employee.address) }
					]}
				/>
			</div>
			<div class="p-4 tablet:p-5">
				<FigureList
					title={text.sections.emergency}
					figures={[
						{ label: text.labels.emergencyName, value: plain(employee.emergency_name) },
						{ label: text.labels.emergencyPhone, value: plain(employee.emergency_phone) },
						{ label: text.labels.emergencyRelation, value: plain(employee.emergency_relation) }
					]}
				/>
			</div>
		</Card>
	</div>

	<ConfirmDialog open={detail.removing} title={text.removeTitle} confirmLabel={text.remove} danger busy={detail.busy} error={detail.actionError} onconfirm={() => void remove()} oncancel={() => detail.closeDialogs()}>
		<p><strong class="text-slate-800">{employee.name || employee.username}</strong> {text.removeLead}</p>
		<p class="mt-2">{text.removeNote}</p>
	</ConfirmDialog>
{:else}
	<Notice loading text={text.loading} />
{/if}
