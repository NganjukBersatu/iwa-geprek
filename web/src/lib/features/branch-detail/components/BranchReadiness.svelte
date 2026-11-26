<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import type { BranchReadiness } from '$lib/api/types';
	import { userMessage } from '$lib/api/user-message';
	import { access } from '$lib/auth/access.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import { canSell, readinessList, type ReadinessItem } from '$lib/features/branch-detail/readiness';
	import { live } from '$lib/live/live';
	import { branchDetailText } from '$lib/text/branch-detail';
	import { format } from '$lib/text/format';

	/** Satu daftar periksa sebelum cabang siap jualan; setiap butir yang kurang menunjuk tempat memperbaikinya. */
	let {
		branchId,
		guideFor
	}: {
		branchId: string;
		/** Nama cabang saat tampil sebagai panduan di dasbor; panduan itu hilang sendiri begitu langkah wajibnya selesai. */
		guideFor?: string;
	} = $props();

	const text = branchDetailText.readiness;

	const TABLES = [
		'outlets',
		'cafe_settings',
		'devices',
		'device_stations',
		'device_station_prints',
		'device_printers',
		'stations',
		'category_stations',
		'category_branch_stations',
		'menu_items',
		'recipe_ingredients',
		'stock_items',
		'payment_methods',
		'users',
		'roles'
	];

	let data = $state<BranchReadiness | null>(null);
	let problem = $state('');

	async function load(): Promise<void> {
		try {
			data = await api.branches.readiness(branchId);
			problem = '';
		} catch (failure) {
			problem = userMessage(failure, text.failed);
		}
	}

	onMount(() => {
		void load();
		return live.on(TABLES, () => void load());
	});

	const list = $derived(data ? readinessList(data, branchId) : null);
	const ready = $derived(list !== null && canSell(list));
	const done = $derived(list ? list.required.filter((item) => item.tone === 'success').length : 0);
	// Di dasbor panduan tidak berkedip saat memuat dan hilang begitu cabang siap jualan.
	const hidden = $derived(guideFor !== undefined && (ready || (!data && !problem)));
	const ICONS = { success: 'circle-check', warning: 'alert-triangle', danger: 'plug-connected-x' } as const;
	const INK = { success: 'text-success-500', warning: 'text-warning-500', danger: 'text-danger-500' } as const;
</script>

{#snippet rows(items: ReadinessItem[])}
	<ul class="flex flex-col gap-3">
		{#each items as item (item.key)}
			<li class="flex flex-col gap-2 tablet:flex-row tablet:items-start tablet:justify-between tablet:gap-3">
				<span class="flex min-w-0 items-start gap-2">
					<i class="ti ti-{ICONS[item.tone]} mt-0.5 shrink-0 {INK[item.tone]}" aria-hidden="true"></i>
					<span class="min-w-0">
						<span class="block text-sm font-semibold text-slate-800">{item.title}</span>
						<span class="block break-words text-xs text-slate-500">{item.detail}</span>
					</span>
				</span>
				<span class="flex flex-wrap gap-x-3 gap-y-1 pl-6 tablet:shrink-0 tablet:flex-col tablet:items-end tablet:pl-0">
					{#each item.fixes.filter((fix) => access.opens(fix.screen)) as fix (fix.href)}
						<a href={fix.href} class="text-xs font-semibold text-brand hover:underline">{fix.label}</a>
					{/each}
				</span>
			</li>
		{/each}
	</ul>
{/snippet}

{#if !hidden}
	<Card>
		<CardHeader
			class="mb-3"
			title={guideFor === undefined ? text.title : text.guideTitle}
			description={guideFor === undefined ? text.description : format(text.guideDescription, { branch: guideFor })}
		/>
		<!-- Lencana di bawah judul, bukan di sampingnya, supaya judul dan deskripsi tidak terdesak di layar HP. -->
		{#if list}
			<div class="mb-4">
				<Badge tone={ready ? 'success' : 'warning'}>
					<i class="ti {ready ? 'ti-circle-check' : 'ti-alert-triangle'}" aria-hidden="true"></i>{ready ? text.ready : format(text.progress, { done, total: list.required.length })}
				</Badge>
			</div>
		{/if}
		{#if problem}
			<Notice text={problem} />
		{:else if !list}
			<Notice text={text.loading} loading />
		{:else}
			<div class="flex flex-col gap-4">
				<section class="flex flex-col gap-2">
					<h3 class="text-xs font-semibold text-slate-500">{text.requiredHeading}</h3>
					{@render rows(list.required)}
				</section>
				{#if guideFor === undefined}
					<section class="flex flex-col gap-2">
						<h3 class="text-xs font-semibold text-slate-500">{text.optionalHeading}</h3>
						{@render rows(list.optional)}
					</section>
				{/if}
				{#if ready}
					<p class="text-xs text-slate-500">{text.nextSteps}</p>
				{/if}
			</div>
		{/if}
	</Card>
{/if}
