<script lang="ts">
	import ReportShell from '$lib/features/report/ReportShell.svelte';
	import ExtrasPanel from '$lib/features/variant/components/ExtrasPanel.svelte';
	import VariantGroups from '$lib/features/variant/components/VariantGroups.svelte';
	import { VariantState } from '$lib/features/variant/variant.svelte';
	import { pageText } from '$lib/text/pages';

	const variant = new VariantState();
</script>

<ReportShell report={variant} title={pageText.optionsTitle} description={pageText.optionsReportDescription}>
	{#snippet children()}
		{#if variant.section === 'varian'}
			<VariantGroups {variant} />
		{:else}
			<ExtrasPanel {variant} />
		{/if}
	{/snippet}
</ReportShell>
