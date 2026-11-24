<script lang="ts">
	/** An action written as a link inside text or a heading, such as "Pilih semua"; its size follows the text around it. */
	let { label, onclick, disabled = false }: { label: string; onclick: () => void; disabled?: boolean } = $props();
</script>

<button type="button" {onclick} {disabled} class="relative min-h-0 min-w-0 text-left font-semibold text-brand after:absolute after:-inset-2 after:content-[''] pointer-fine:after:hidden underline-offset-2 hover:underline disabled:opacity-50">{label}</button>
