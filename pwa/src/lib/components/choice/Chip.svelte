<script lang="ts">
	let { label, selected, onclick }: { label: string; selected: boolean; onclick: () => void } = $props();
</script>

<button
	type="button"
	role="tab"
	aria-selected={selected}
	{onclick}
	class="text-label flex min-h-[var(--size-control)] items-center justify-center rounded-full border px-4 {selected ? 'border-primary bg-primary text-on-primary' : 'border-divider bg-surface text-content'}"
>
	{label}
</button>
