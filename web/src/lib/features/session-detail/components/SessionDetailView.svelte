<script lang="ts">
	import { PAGES } from '$lib/nav/pages';
	import { goto } from '$app/navigation';
	import { onMount, untrack } from 'svelte';
	import { api } from '$lib/api';
	import { ApiError } from '$lib/api/http';
	import { userMessage } from '$lib/api/user-message';
	import type { SessionCorrection } from '$lib/api/types';
	import { toast } from '$lib/components/feedback/toast.svelte';
	import { editAddress } from '../../record-detail/edit-address.svelte';
	import SessionCorrectionForm from '../../session-history/components/SessionCorrectionForm.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import PageIntro from '$lib/components/header/PageIntro.svelte';
	import Tabs from '$lib/components/tabs/Tabs.svelte';
	import { formatDateTime } from '$lib/format/datetime';
	import { live } from '$lib/live/live';
	import { enter } from '$lib/motion/transitions';
	import { SALES_TABLES } from '$lib/live/tables';
	import type { SessionDetailState } from '../session-detail.svelte';
	import ExpensesPanel from './ExpensesPanel.svelte';
	import OpenBillsPanel from './OpenBillsPanel.svelte';
	import OrdersPanel from './OrdersPanel.svelte';
	import SessionManage from './SessionManage.svelte';
	import SessionSummary from './SessionSummary.svelte';
	import SessionChangesPanel from '../../money-changes/components/SessionChangesPanel.svelte';
	import { SessionChangesState } from '../../money-changes/session-changes.svelte';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { sessionDetailText } from '$lib/text/session-detail';
	import { format } from '$lib/text/format';

	const LIST_PATH = PAGES.sessionHistory.path;

	let { session }: { session: SessionDetailState } = $props();

	const address = editAddress();
	let saving = $state(false);
	let saveError = $state('');
	let saveFieldErrors = $state<Record<string, string>>({});

	async function correct(body: SessionCorrection): Promise<void> {
		saving = true;
		saveError = '';
		saveFieldErrors = {};
		try {
			await api.sessions.correct(session.id, body);
			toast.show(sessionDetailText.sessionCorrected);
			await session.refresh();
			void goto(address.recordPath);
		} catch (problem) {
			saveFieldErrors = problem instanceof ApiError ? problem.fieldErrors : {};
			saveError = userMessage(problem, sessionDetailText.sessionCorrectFailed);
		} finally {
			saving = false;
		}
	}

	const changes = new SessionChangesState(untrack(() => session.id));

	const row = $derived(session.row);
	const tabs = $derived([
		{ key: 'orders', label: termText.transaction, count: session.orders?.length },
		{ key: 'expenses', label: termText.expense, count: session.expenses?.length },
		{ key: 'changes', label: sessionDetailText.changes, count: changes.data?.total }
	]);

	onMount(() => {
		void session.load();
		void changes.load();
		return live.on(SALES_TABLES, () => {
			void session.refresh();
			void changes.refresh();
		});
	});
</script>

{#if session.error}
	<Banner tone="danger" icon="alert-triangle" title={sessionDetailText.sessionLoadFailedTitle}>
		{session.error}
		{#snippet action()}
			<Button label={actionText.retry} onclick={() => void session.load()} />
		{/snippet}
	</Banner>
{:else if row && address.editing}
	<SessionCorrectionForm {row} busy={saving} error={saveError} fieldErrors={saveFieldErrors} onsave={(body) => void correct(body)} onclose={() => void goto(address.recordPath)} />
{:else if row}
	<div class="flex flex-col gap-4 tablet:gap-6">
		<PageIntro
			title={format(sessionDetailText.sessionTitle, { name: row.cashier_username })}
			description={format(sessionDetailText.openedAtBy, { shift: row.shift_code ? format(sessionDetailText.shiftPrefix, { code: row.shift_code }) : '', time: formatDateTime(row.opened_at), status: row.closed_at ? format(sessionDetailText.closedAt, { time: formatDateTime(row.closed_at) }) : sessionDetailText.stillRunning })}
			items={[{ label: PAGES.sessionHistory.label, href: LIST_PATH }, { label: format(sessionDetailText.sessionOf, { name: row.cashier_username }) }]}
		>
			{#snippet badge()}
				{#if row.running}<Badge tone="success">{termText.running}</Badge>{/if}
			{/snippet}
			{#snippet actions()}
				<SessionManage {row} onchanged={() => void session.refresh()} ondeleted={() => void goto(LIST_PATH)} />
			{/snippet}
		</PageIntro>

		<SessionSummary {row} />

		{#if session.openBills.length > 0}
			<OpenBillsPanel bills={session.openBills} />
		{/if}

		<Card flush>
			<Tabs {tabs} label={sessionDetailText.sessionContents} bind:value={() => session.tab, (key) => session.setTab(key)} />
			{#key session.tab}
				<div in:enter>
					{#if session.tab === 'orders'}
						<OrdersPanel {session} {row} />
					{:else if session.tab === 'changes'}
						<SessionChangesPanel {changes} />
					{:else}
						<ExpensesPanel {session} {row} />
					{/if}
				</div>
			{/key}
		</Card>
	</div>
{:else}
	<Notice loading text={sessionDetailText.sessionLoading} />
{/if}
