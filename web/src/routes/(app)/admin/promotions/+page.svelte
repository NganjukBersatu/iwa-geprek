<script lang="ts">
	import MoreButton from '$lib/components/button/MoreButton.svelte';
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import PromotionsView from '$lib/features/promotions/components/PromotionsView.svelte';
	import { PromotionsState } from '$lib/features/promotions/promotions.svelte';
	import { pageText } from '$lib/text/pages';

	const promotions = new PromotionsState();
</script>

<ManageShell manage={promotions} title={pageText.promotionsTitle} description={pageText.promotionsDescription} loadingText={pageText.loadingPromotions}>
	{#snippet actions()}
		<MoreButton selection={[promotions.selection, promotions.announcementSelection]} />
	{/snippet}
	{#snippet children()}
		<PromotionsView {promotions} />
	{/snippet}
</ManageShell>
