<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import type { CodeGroupCreate } from '$lib/api/types';
	import { userMessage } from '$lib/api/user-message';
	import Banner from '$lib/components/card/Banner.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import BulkEntryDialog from '$lib/components/dialog/BulkEntryDialog.svelte';
	import type { Field } from '$lib/components/form/types';
	import { PAGES } from '$lib/nav/pages';
	import { branchList } from '$lib/stores/branch';
	import { ALL_BRANCHES } from '../all-branches';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { shiftCodeText } from '$lib/text/shift-codes';

	let outlets = $state<{ id: string; name: string }[] | null>(null);
	let error = $state('');

	async function load(): Promise<void> {
		error = '';
		try {
			outlets = (await branchList()).map((outlet) => ({ id: outlet.id, name: outlet.name }));
		} catch (cause) {
			error = userMessage(cause, shiftCodeText.branchesLoadFailed);
		}
	}

	onMount(() => void load());

	const entryColumns = $derived<Field[]>([
		{ key: 'category', label: termText.category, required: true },
		{ key: 'code', label: termText.code, required: true },
		{ key: 'start_clock', label: shiftCodeText.startTime, placeholder: 'HH:MM' },
		{ key: 'end_clock', label: shiftCodeText.endTime, placeholder: 'HH:MM' },
		{ key: 'crosses_midnight', label: shiftCodeText.crossesMidnight, kind: 'select', options: [{ value: 'yes', label: termText.yes }, { value: 'no', label: shiftCodeText.no }] },
		{ key: 'overtime_start_clock', label: shiftCodeText.overtimeStart, placeholder: 'HH:MM' },
		{ key: 'overtime_end_clock', label: shiftCodeText.overtimeEnd, placeholder: 'HH:MM' },
		{ key: 'color', label: shiftCodeText.color, placeholder: '#RRGGBB' },
		{ key: 'is_day_off', label: termText.dayOff, kind: 'select', options: [{ value: 'yes', label: termText.yes }, { value: 'no', label: shiftCodeText.no }] },
		{ key: 'sort_order', label: shiftCodeText.order, kind: 'number', placeholder: '0' },
		{ key: 'outlet', label: termText.branch, kind: 'select', options: [{ value: ALL_BRANCHES, label: termText.allBranches }, ...(outlets ?? []).map((outlet) => ({ value: outlet.id, label: outlet.name }))] }
	]);

	/** A row of the entry table to a new code: [outlet] is one branch, or every branch when it is "all". */
	function createMany(rows: Record<string, string | number>[]) {
		const items: CodeGroupCreate[] = rows.map((row) => ({
			category: String(row['category']),
			code: String(row['code']),
			start_clock: row['start_clock'] ? String(row['start_clock']) : null,
			end_clock: row['end_clock'] ? String(row['end_clock']) : null,
			overtime_start_clock: row['overtime_start_clock'] ? String(row['overtime_start_clock']) : null,
			overtime_end_clock: row['overtime_end_clock'] ? String(row['overtime_end_clock']) : null,
			color: row['color'] ? String(row['color']) : null,
			is_day_off: row['is_day_off'] === 'yes',
			crosses_midnight: row['crosses_midnight'] === 'yes',
			sort_order: typeof row['sort_order'] === 'number' ? row['sort_order'] : 0,
			outlet_ids: row['outlet'] === ALL_BRANCHES || !row['outlet'] ? (outlets ?? []).map((outlet) => outlet.id) : [String(row['outlet'])]
		}));
		return api.shiftCodes.bulk.create(items);
	}
</script>

{#if error}
	<Banner tone="danger" icon="alert-triangle" title={actionText.pageLoadFailed}>
		{error}
		{#snippet action()}
			<Button label={actionText.retry} onclick={() => void load()} />
		{/snippet}
	</Banner>
{:else if outlets}
	<BulkEntryDialog
		asPage
		title={shiftCodeText.bulkTitle}
		hint={shiftCodeText.bulkHint}
		columns={entryColumns}
		submit={createMany}
		submitLabel="Simpan semua kode"
		onclose={() => void goto(PAGES.shiftCodes.path)}
	/>
{:else}
	<Notice loading text={shiftCodeText.branchesLoading} />
{/if}
