<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	/** Lencana kode (misalnya kode shift) dengan titik warna yang ditentukan pengguna. */
	let { text, color }: { text: string; color: string | null } = $props();
</script>

<span class="text-label inline-flex items-center gap-1 rounded-full bg-selected px-3 py-1 text-content">
	<span class="size-2 rounded-full {color ? '' : 'bg-content-muted'}" use:dynamicStyle={{ 'background-color': color }}></span>
	{text}
</span>
