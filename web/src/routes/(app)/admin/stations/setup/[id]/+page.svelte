<script lang="ts">
	import { page } from '$app/state';
	import StationEditView from '$lib/features/stations/components/StationEditView.svelte';
	import { StationEditState } from '$lib/features/stations/station-edit.svelte';

	// Setelah stasiun baru dibuat, alamat pindah ke stasiun itu di rute yang sama, jadi halaman dibangun ulang mengikuti alamatnya.
	const edit = $derived(new StationEditState(page.params['id'] as string));
</script>

{#key edit}
	<StationEditView {edit} />
{/key}
