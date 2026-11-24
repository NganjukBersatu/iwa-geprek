<script lang="ts">
	import { page } from '$app/state';
	import BranchPeriodDetailView from '$lib/features/branch-periods/components/BranchPeriodDetailView.svelte';
	import { BranchPeriodDetailState } from '$lib/features/branch-periods/branch-period-detail.svelte';

	// Menyimpan tanggal mulai baru pindah ke alamat lain di rute yang sama, jadi halaman dibangun ulang mengikuti alamatnya.
	const detail = $derived(new BranchPeriodDetailState(page.params['outlet'] as string, page.params['start'] as string));
</script>

{#key detail}
	<BranchPeriodDetailView {detail} />
{/key}
