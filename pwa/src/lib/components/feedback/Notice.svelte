<script lang="ts">
	/** Keterangan keadaan kosong, memuat, atau gagal; satu kalimat di tengah. */
	let { text, class: className = '' }: { text: string; class?: string } = $props();
</script>

<p class="text-body m-0 w-full py-6 text-center text-content-muted {className}">{text}</p>
