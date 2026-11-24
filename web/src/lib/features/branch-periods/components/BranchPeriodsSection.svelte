<script lang="ts">
	import ManageSection from '$lib/features/manage/ManageSection.svelte';
	import { branchPeriodText as text } from '$lib/text/branch-periods';
	import { BranchPeriodsState } from '../branch-periods.svelte';
	import BranchPeriodsView from './BranchPeriodsView.svelte';

	/** `onedit` hanya ada untuk peran yang boleh mengubah cabang; membuka dialog periode berjalan milik halaman cabang. */
	let { onedit }: { onedit?: () => void } = $props();

	/** Periode satu cabang di halaman detail cabang; cabangnya dibaca dari pilihan cabang yang sudah ditetapkan halaman itu. */
	const periods = new BranchPeriodsState();
</script>

<ManageSection manage={periods} loadingText={text.loading}>
	<BranchPeriodsView {periods} {onedit} />
</ManageSection>
