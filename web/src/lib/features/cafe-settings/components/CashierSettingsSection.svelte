<script lang="ts">
	import ManageSection from '$lib/features/manage/ManageSection.svelte';
	import { cafeSettingsText as text } from '$lib/text/cafe-settings';
	import { CafeSettingsState } from '../cafe-settings.svelte';
	import CashierSettingsView from './CashierSettingsView.svelte';

	const cafe = new CafeSettingsState();
</script>

<ManageSection manage={cafe} loadingText={text.cashierLoading}>
	<CashierSettingsView {cafe} />
</ManageSection>
