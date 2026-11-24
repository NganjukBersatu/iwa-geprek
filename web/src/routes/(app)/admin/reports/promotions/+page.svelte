<script lang="ts">
	import PromoView from '$lib/features/promo/components/PromoView.svelte';
	import { PromoState } from '$lib/features/promo/promo.svelte';
	import ReportShell from '$lib/features/report/ReportShell.svelte';
	import { pageText } from '$lib/text/pages';

	const promo = new PromoState();
</script>

<ReportShell report={promo} title={pageText.promoReportTitle} description={pageText.promoReportDescription}>
	{#snippet children(data)}
		<PromoView {data} {promo} />
	{/snippet}
</ReportShell>
