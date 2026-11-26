<script lang="ts">
	import { page } from '$app/state';
	import { access } from '$lib/auth/access.svelte';
	import AttendanceRulesSection from '$lib/features/attendance-rules/components/AttendanceRulesSection.svelte';
	import BranchPeriodsSection from '$lib/features/branch-periods/components/BranchPeriodsSection.svelte';
	import BranchDetailView from '$lib/features/branch-detail/components/BranchDetailView.svelte';
	import BranchSummary from '$lib/features/branch-detail/components/BranchSummary.svelte';
	import { BranchDetailState } from '$lib/features/branch-detail/branch-detail.svelte';
	import CashierSettingsSection from '$lib/features/cafe-settings/components/CashierSettingsSection.svelte';
	import PricingSettingsSection from '$lib/features/cafe-settings/components/PricingSettingsSection.svelte';
	import ReceiptSettingsSection from '$lib/features/cafe-settings/components/ReceiptSettingsSection.svelte';
	import DevicesSection from '$lib/features/devices/components/DevicesSection.svelte';
	import PrintersSection from '$lib/features/printers/components/PrintersSection.svelte';
	import { BRANCH_TABS, PAGES, branchPath, type BranchTab } from '$lib/nav/pages';
	import { branchDetailText } from '$lib/text/branch-detail';
	import { goto } from '$app/navigation';

	// Pindah ke cabang lain lewat alamat membangun ulang halaman, supaya setiap bagian memuat cabang yang benar.
	const detail = $derived(new BranchDetailState(page.params['id'] as string));

	// Bagian yang izinnya tidak dimiliki peran ini tidak ditampilkan sama sekali.
	const tabs = $derived<{ key: BranchTab; label: string }[]>([
		{ key: BRANCH_TABS.summary, label: branchDetailText.tabs.summary },
		{ key: BRANCH_TABS.periods, label: branchDetailText.tabs.periods },
		...(access.opens(PAGES.cafeSettings.screen)
			? [
					{ key: BRANCH_TABS.receipt, label: branchDetailText.tabs.receipt },
					{ key: BRANCH_TABS.pricing, label: branchDetailText.tabs.pricing },
					{ key: BRANCH_TABS.cashier, label: branchDetailText.tabs.cashier }
				]
			: []),
		...(access.opens(PAGES.attendanceRules.screen) ? [{ key: BRANCH_TABS.rules, label: branchDetailText.tabs.rules }] : []),
		...(access.opens(PAGES.devices.screen) ? [{ key: BRANCH_TABS.devices, label: branchDetailText.tabs.devices }] : []),
		...(access.opens(PAGES.printers.screen) ? [{ key: BRANCH_TABS.printers, label: branchDetailText.tabs.printers }] : [])
	]);

	// Periode berjalan diubah lewat halaman edit cabang, tempat pola tanggal tutup bukunya diatur.
	const editRunningPeriod = $derived(access.allows('manage_branches') ? () => void goto(`${branchPath(detail.id)}/edit`) : undefined);
</script>

{#key detail}
	<BranchDetailView {detail} {tabs}>
		{#snippet children(tab)}
			{#if tab === BRANCH_TABS.summary && detail.branch}
				<BranchSummary branch={detail.branch} />
			{:else if tab === BRANCH_TABS.periods}
				<BranchPeriodsSection onedit={editRunningPeriod} />
			{:else if tab === BRANCH_TABS.receipt}
				<ReceiptSettingsSection />
			{:else if tab === BRANCH_TABS.pricing}
				<PricingSettingsSection />
			{:else if tab === BRANCH_TABS.cashier}
				<CashierSettingsSection />
			{:else if tab === BRANCH_TABS.rules}
				<AttendanceRulesSection />
			{:else if tab === BRANCH_TABS.devices}
				<DevicesSection />
			{:else if tab === BRANCH_TABS.printers}
				<PrintersSection />
			{/if}
		{/snippet}
	</BranchDetailView>
{/key}
