<script lang="ts">
	import { termText } from '$lib/text/terms';
	import { whenChanged } from '$lib/stores/when-changed.svelte';
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import Tabs from '$lib/components/tabs/Tabs.svelte';
	import CancellationsPanel from '$lib/features/cancellations/components/CancellationsPanel.svelte';
	import { CancellationsState } from '$lib/features/cancellations/cancellations.svelte';
	import { CANCELLATIONS_TAB } from '$lib/nav/pages';
	import ReportShell from '$lib/features/report/ReportShell.svelte';
	import SessionHistoryView from '$lib/features/session-history/components/SessionHistoryView.svelte';
	import { SessionHistoryState } from '$lib/features/session-history/session-history.svelte';
	import { live } from '$lib/live/live';
	import { enter } from '$lib/motion/transitions';
	import { pageText } from '$lib/text/pages';

	const SESSIONS_TAB = 'sesi';

	const history = new SessionHistoryState();
	const cancellations = new CancellationsState();

	let tab = $state(page.url.searchParams.get('tab') === CANCELLATIONS_TAB ? CANCELLATIONS_TAB : SESSIONS_TAB);

	const tabs = $derived([
		{ key: SESSIONS_TAB, label: termText.cashierSession },
		...(cancellations.canDecide ? [{ key: CANCELLATIONS_TAB, label: pageText.cancellationRequests, count: cancellations.loaded ? cancellations.total : undefined }] : [])
	]);

	whenChanged(() => history.query.branch, () => void cancellations.queryChanged());
	onMount(() => live.on(cancellations.tables, () => void cancellations.refresh()));
</script>

<ReportShell report={history} title={pageText.sessionHistoryTitle} description={pageText.sessionHistoryDescription}>
	{#snippet children(data)}
		{#if cancellations.canDecide}<Tabs {tabs} label={pageText.pageContents} bind:value={tab} class="mb-4" />{/if}
		{#key tab}
			<div in:enter>
				{#if tab === CANCELLATIONS_TAB && cancellations.canDecide}
					<CancellationsPanel {cancellations} allBranches={history.query.branch === null} />
				{:else}
					<SessionHistoryView {data} {history} />
				{/if}
			</div>
		{/key}
	{/snippet}
</ReportShell>
