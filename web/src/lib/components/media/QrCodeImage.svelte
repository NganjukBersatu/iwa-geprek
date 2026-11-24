<script lang="ts">
	import { QrCode } from '@skeletonlabs/skeleton-svelte';

	/** Gambar kode QR dari teks; label wajib supaya pembaca layar tahu isinya. */
	let { value, label }: { value: string; label: string } = $props();
</script>

<QrCode {value} class="size-32 shrink-0 rounded-xl bg-white p-2 text-slate-800" role="img" aria-label={label}>
	<QrCode.Frame class="size-full fill-current">
		<QrCode.Pattern />
	</QrCode.Frame>
</QrCode>
