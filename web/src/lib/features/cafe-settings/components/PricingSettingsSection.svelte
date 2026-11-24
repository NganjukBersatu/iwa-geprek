<script lang="ts">
	import ManageSection from '$lib/features/manage/ManageSection.svelte';
	import { cafeSettingsText as text } from '$lib/text/cafe-settings';
	import { CafeSettingsState } from '../cafe-settings.svelte';
	import PricingSettingsView from './PricingSettingsView.svelte';

	const cafe = new CafeSettingsState();
</script>

<ManageSection manage={cafe} loadingText={text.pricesLoading}>
	<PricingSettingsView {cafe} />
</ManageSection>
