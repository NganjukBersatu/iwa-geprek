<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import type { AssignmentCreate, PoolUser, Role, ShiftCode } from '$lib/api/types';
	import { userMessage } from '$lib/api/user-message';
	import Banner from '$lib/components/card/Banner.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import BulkEntryDialog from '$lib/components/dialog/BulkEntryDialog.svelte';
	import type { Field } from '$lib/components/form/types';
	import { assignableRoles } from '$lib/features/roles/assignable';
	import { PAGES } from '$lib/nav/pages';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { scheduleText } from '$lib/text/schedule';

	let pool = $state<PoolUser[] | null>(null);
	let codes = $state<ShiftCode[]>([]);
	let roles = $state<Role[]>([]);
	/** The branch picked on the page; it decides which people and codes the rows may use. */
	let branch = $state('');
	let error = $state('');

	async function load(): Promise<void> {
		error = '';
		try {
			const [foundPool, foundCodes, foundRoles] = await Promise.all([api.schedule.pool(), api.schedule.codes(), api.roles.list()]);
			pool = foundPool;
			codes = foundCodes;
			roles = foundRoles;
		} catch (cause) {
			error = userMessage(cause, scheduleText.contextLoadFailed);
		}
	}

	onMount(() => void load());

	const people = $derived((pool ?? []).filter((person) => person.outlet_id === branch));
	const workCodes = $derived(codes.filter((code) => !code.is_day_off && code.outlet_id === branch));
	const entryColumns = $derived<Field[]>([
		{ key: 'user_id', label: termText.employee, kind: 'select', required: true, options: people.map((person) => ({ value: person.id, label: person.name || person.username })) },
		{ key: 'date', label: termText.date, kind: 'date', required: true },
		{ key: 'shift_code_id', label: scheduleText.shiftCode, kind: 'select', required: true, options: workCodes.map((code) => ({ value: code.id, label: code.code })) },
		{ key: 'role_id', label: scheduleText.dayRole, kind: 'select', options: assignableRoles(roles).map((role) => ({ value: role.id, label: role.name })) },
		{ key: 'note', label: termText.note }
	]);
</script>

{#if error}
	<Banner tone="danger" icon="alert-triangle" title={actionText.pageLoadFailed}>
		{error}
		{#snippet action()}
			<Button label={actionText.retry} onclick={() => void load()} />
		{/snippet}
	</Banner>
{:else if pool}
	<BulkEntryDialog
		asPage
		title={scheduleText.bulkTitle}
		hint={scheduleText.bulkHint}
		columns={entryColumns}
		withBranch
		onbranch={(outletId) => (branch = outletId)}
		submit={(rows, outletId) => api.schedule.assignments.bulk.createIn(outletId, rows as unknown as AssignmentCreate[])}
		submitLabel="Simpan semua jadwal"
		onclose={() => void goto(PAGES.schedule.path)}
	/>
{:else}
	<Notice loading text={scheduleText.contextLoading} />
{/if}
