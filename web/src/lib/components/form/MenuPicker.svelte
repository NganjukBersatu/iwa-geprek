<script lang="ts">
	import CheckRow from '$lib/components/form/CheckRow.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import type { SvelteSet } from 'svelte/reactivity';
	import { controlText } from '$lib/text/controls';
	import { format } from '$lib/text/format';

	let { menus, chosen, label }: { menus: { id: string; name: string }[]; chosen: SvelteSet<string>; label: string } = $props();

	let search = $state('');
	const shown = $derived(menus.filter((menu) => menu.name.toLowerCase().includes(search.trim().toLowerCase())));
	const toggle = (id: string) => (chosen.has(id) ? chosen.delete(id) : chosen.add(id));
</script>

<section class="flex flex-col gap-2">
	<div class="flex items-center justify-between gap-2">
		<h3 class="text-xs font-semibold text-slate-600">{format(controlText.menusChosen, { label: label, count: chosen.size })}</h3>
		{#if chosen.size > 0}
			<button type="button" class="text-xs font-semibold text-brand hover:underline" onclick={() => chosen.clear()}>{controlText.clear}</button>
		{/if}
	</div>
	<TextField label={controlText.searchMenu} bind:value={search} />
	<div class="grid max-h-56 gap-1 overflow-y-auto tablet:grid-cols-2">
		{#each shown as menu (menu.id)}
			<CheckRow label={menu.name} checked={chosen.has(menu.id)} onchange={() => toggle(menu.id)} />
		{/each}
	</div>
</section>
