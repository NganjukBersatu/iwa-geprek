<script lang="ts">
	import SearchBox from './SearchBox.svelte';

	let {
		value,
		placeholder,
		label,
		divided = true,
		onsearch
	}: {
		value: string;
		placeholder: string;
		label: string;
		divided?: boolean;
		onsearch: (query: string) => void;
	} = $props();
</script>

<!-- A list's search row, kept outside Filter: it never shows as a chip or counts as a filter. -->
<div class="px-4 py-3 tablet:px-5 {divided ? 'border-b border-slate-100' : ''}">
	<SearchBox {value} {placeholder} {label} onsearch={(query) => onsearch(query.trim())} />
</div>
