<script lang="ts">
	import ManageSection from '$lib/features/manage/ManageSection.svelte';
	import { printerText as text } from '$lib/text/printers';
	import { PrintersState } from '../printers.svelte';
	import PrintersView from './PrintersView.svelte';

	/** Printer satu cabang di halaman detail cabang; cabangnya dibaca dari pilihan cabang yang sudah ditetapkan halaman itu. */
	const printers = new PrintersState();
</script>

<ManageSection manage={printers} loadingText={text.loading}>
	<PrintersView {printers} />
</ManageSection>
