<script lang="ts">
	import MoreButton from '$lib/components/button/MoreButton.svelte';
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import { performanceExportColumns } from '$lib/features/user-performance/columns';
	import UserPerformanceView from '$lib/features/user-performance/components/UserPerformanceView.svelte';
	import { RANGE_LABELS } from '$lib/features/user-performance/labels';
	import { UserPerformanceState } from '$lib/features/user-performance/user-performance.svelte';
	import { userPerformanceText as t } from '$lib/text/user-performance';

	const performance = new UserPerformanceState();
</script>

<ManageShell manage={performance} filters={performance.filters} title={t.pageTitle} description={t.pageDescription} loadingText={t.loading}>
	{#snippet actions()}
		<MoreButton exporter={{ title: `${t.exportTitle} ${RANGE_LABELS[performance.range]}`, columns: performanceExportColumns, rows: () => performance.exportRows() }} />
	{/snippet}
	{#snippet children()}
		<UserPerformanceView {performance} />
	{/snippet}
</ManageShell>
