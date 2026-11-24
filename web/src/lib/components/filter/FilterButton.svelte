<script lang="ts">
	import { Popover, Portal } from '@skeletonlabs/skeleton-svelte';
	import { controlSize, secondaryStyle } from '../button/button-style';
	import { unfold } from '$lib/motion/transitions';
	import { DATE_PRESETS } from '$lib/date/range';
	import SearchBox from './SearchBox.svelte';
	import DateRangePanel from './DateRangePanel.svelte';
	import type { Filters } from './filters.svelte';
	import type { FilterDef } from './types';
	import { controlText } from '$lib/text/controls';
	import { format } from '$lib/text/format';

	let { filters, label = controlText.filter }: { filters: Filters; label?: string } = $props();

	let open = $state(false);
	let term = $state('');
	let activeKey = $state<string | null>(null);
	let calendar = $state(false);

	type Hit = { id: string; title: string; context: string | null; run: () => void };

	const query = $derived(term.trim().toLowerCase());
	const hits = $derived.by((): Hit[] => {
		if (!query) return [];
		const result: Hit[] = [];
		for (const def of filters.offered) {
			if (def.label.toLowerCase().includes(query)) {
				result.push({ id: def.key, title: def.label, context: null, run: () => openDef(def.key, false) });
			}
			if (def.kind === 'select') {
				for (const option of def.options) {
					if (!option.label.toLowerCase().includes(query)) continue;
					result.push({ id: `${def.key}:${option.value}`, title: option.label, context: def.label, run: () => choose(def.key, option.value) });
				}
			} else if (def.kind === 'date') {
				for (const preset of def.presets ?? DATE_PRESETS) {
					if (!preset.label.toLowerCase().includes(query)) continue;
					result.push({ id: `${def.key}:${preset.value}`, title: preset.label, context: def.label, run: () => choose(def.key, { preset: preset.value }) });
				}
				if ('pilih tanggal'.includes(query)) {
					result.push({ id: `${def.key}:custom`, title: controlText.chooseDate, context: def.label, run: () => openDef(def.key, true) });
				}
			}
		}
		return result;
	});

	function reset(): void {
		term = '';
		activeKey = null;
		calendar = false;
	}

	function handleOpenChange(details: { open: boolean }): void {
		open = details.open;
		if (!details.open) reset();
	}

	function close(): void {
		open = false;
		reset();
	}

	function openDef(key: string, withCalendar: boolean): void {
		term = '';
		activeKey = key;
		calendar = withCalendar;
	}

	function toggle(def: FilterDef): void {
		activeKey = activeKey === def.key ? null : def.key;
		calendar = false;
	}

	function choose(key: string, value: Parameters<Filters['set']>[1]): void {
		filters.set(key, value);
		close();
	}

	function clearAll(): void {
		filters.clearAll();
		close();
	}

	function isPreset(key: string, preset: string): boolean {
		const current = filters.pick(key);
		return !!current && typeof current === 'object' && 'preset' in current && current.preset === preset;
	}

	function isCustom(key: string): boolean {
		const current = filters.pick(key);
		return !!current && typeof current === 'object' && 'from' in current;
	}

	const rowClass = 'flex w-full min-h-0 items-center justify-between gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors motion-reduce:transition-none';
	const idle = 'text-slate-600 hover:bg-brand-soft';
	const selected = 'bg-brand-soft font-semibold text-brand';
</script>

<Popover {open} onOpenChange={handleOpenChange} positioning={{ placement: 'bottom-end' }}>
	<Popover.Trigger
		class="btn btn-sm shrink-0 font-semibold hover:brightness-100 {controlSize} {secondaryStyle}"
	>
		<i class="ti ti-filter text-sm" aria-hidden="true"></i>
		<span>{label}</span>
		{#if filters.count > 0}
			<span class="rounded-full bg-brand px-2 text-xs leading-5 text-white">{filters.count}</span>
		{/if}
	</Popover.Trigger>

	<Portal>
		<Popover.Positioner>
			<!-- The positioner copies its z-index from the content, so the layer is set here. -->
			<Popover.Content class="z-50 outline-none">
				<div class="flex max-h-[min(80dvh,34rem)] w-80 max-w-[calc(100vw-2rem)] flex-col gap-1 overflow-y-auto rounded-lg border border-brand-line bg-white p-2 shadow-xl">
					<SearchBox bind:value={term} placeholder={controlText.searchFilterPlaceholder} label={controlText.searchFilter} delay={0} />

					{#if query}
						<ul class="flex flex-col gap-0.5">
							{#each hits as hit (hit.id)}
								<li>
									<button type="button" onclick={hit.run} class="{rowClass} {idle}">
										<span class="truncate">{hit.title}</span>
										{#if hit.context}
											<span class="shrink-0 text-xs text-slate-500">{hit.context}</span>
										{/if}
									</button>
								</li>
							{:else}
								<li class="px-3 py-2 text-sm text-slate-500">{format(controlText.noOptionMatches, { term: term.trim() })}</li>
							{/each}
						</ul>
					{:else}
					<ul class="flex flex-col gap-0.5">
						{#each filters.offered as def (def.key)}
							{@const isOpen = activeKey === def.key}
							{@const current = filters.text(def.key)}
							<li>
								<button
									type="button"
									onclick={() => toggle(def)}
									aria-expanded={isOpen}
									class="{rowClass} {isOpen ? selected : idle}"
								>
									<span>{def.label}</span>
									<span class="ml-auto flex min-w-0 items-center gap-2">
										{#if current}
											<span class="truncate text-xs font-normal text-slate-500">{current}</span>
										{/if}
										<i class="ti ti-chevron-down shrink-0 text-slate-400 transition-transform duration-200 motion-reduce:transition-none {isOpen ? 'rotate-180' : ''}" aria-hidden="true"></i>
									</span>
								</button>

								{#if isOpen}
									<div transition:unfold>
										<div class="ml-3 mt-1 flex flex-col gap-0.5 border-l border-brand-line/60 pb-1 pl-2">
											{#if def.kind === 'select'}
												{#each def.options as option (option.value)}
													<button
														type="button"
														onclick={() => choose(def.key, option.value)}
														class="{rowClass} {filters.get(def.key) === option.value ? selected : idle}"
													>
														{option.label}
													</button>
												{/each}
											{:else}
												{#each def.presets ?? DATE_PRESETS as preset (preset.value)}
													<button
														type="button"
														onclick={() => choose(def.key, { preset: preset.value })}
														class="{rowClass} {isPreset(def.key, preset.value) ? selected : idle}"
													>
														{preset.label}
													</button>
												{/each}
												<button
													type="button"
													onclick={() => (calendar = !calendar)}
													aria-expanded={calendar}
													class="{rowClass} {calendar || isCustom(def.key) ? selected : idle}"
												>
													<span>{controlText.chooseDate}</span>
													<i class="ti ti-chevron-down text-slate-400 transition-transform duration-200 motion-reduce:transition-none {calendar ? 'rotate-180' : ''}" aria-hidden="true"></i>
												</button>
											{/if}
										</div>
										{#if def.kind === 'date' && calendar}
											<div transition:unfold class="mb-1 rounded-lg border border-brand-line/60 p-2">
												<DateRangePanel
													value={filters.range(def.key)}
													reach={def.reach}
													onselect={(range) => choose(def.key, range)}
												/>
											</div>
										{/if}
									</div>
								{/if}
							</li>
						{/each}
					</ul>
					{/if}

					<div class="border-t border-brand-line/60 pt-1">
						<button
							type="button"
							onclick={clearAll}
							disabled={filters.count === 0}
							class="{rowClass} font-semibold text-brand hover:bg-brand-soft disabled:opacity-40 disabled:hover:bg-transparent"
						>
							{controlText.clearAllFilters}
						</button>
					</div>
				</div>
			</Popover.Content>
		</Popover.Positioner>
	</Portal>
</Popover>
