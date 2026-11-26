<script lang="ts">
	import { dynamicStyle } from '$lib/motion/actions';
	import ProgressLine from '$lib/components/motion/ProgressLine.svelte';
	import Skeleton from '$lib/components/skeleton/Skeleton.svelte';
	import { tick } from 'svelte';
	import { controlText } from '$lib/text/controls';
	import { format } from '$lib/text/format';

	let {
		value = $bindable(''),
		options,
		empty,
		id,
		disabled = false,
		size = 'md',
		invalid = false,
		describedby,
		class: className = '',
		'aria-label': ariaLabel,
		onchange,
		onsearch,
		onmore,
		searching = false,
		loadingMore = false
	}: {
		value?: string;
		options: { value: string; label: string }[];
		/** A first choice with an empty value, also shown greyed in the closed box while nothing is picked. */
		empty?: string;
		id?: string;
		disabled?: boolean;
		/** md for ordinary fields; sm for filters and dense rows. */
		size?: 'md' | 'sm';
		/** The choice is wrong or missing: the box gets a red edge. */
		invalid?: boolean;
		describedby?: string;
		/** Layout only (w-full, flex-1, ...); the look of the box follows `size`. */
		class?: string;
		'aria-label'?: string;
		onchange?: (value: string) => void;
		/** Bila diisi, kata cari dikirim ke pemanggil (misalnya ke server) dan `options` ditampilkan apa adanya. */
		onsearch?: (text: string) => void;
		/** Dipanggil saat daftar digulir mendekati akhir, supaya pemanggil memuat halaman berikutnya. */
		onmore?: () => void;
		/** Hasil cari sedang ditunggu dari pemanggil: daftar diganti kerangka di bawah garis progres. */
		searching?: boolean;
		/** Halaman berikutnya sedang dimuat: kerangka di ujung bawah daftar dan garis progres. */
		loadingMore?: boolean;
	} = $props();

	type Choice = { value: string; label: string; blank: boolean };

	// A long list can be searched by typing; a short one stays a plain list, since a phone keyboard for four choices only gets in the way.
	const SEARCH_FROM = 8;
	// Jarak dari ujung bawah daftar saat halaman berikutnya mulai diminta, kira-kira tiga baris.
	const MORE_BEFORE_PX = 100;
	const SEARCH_SKELETON_ROWS = 3;
	const MORE_SKELETON_ROWS = 2;

	let button = $state<HTMLButtonElement | null>(null);
	let list = $state<HTMLDivElement | null>(null);
	let search = $state<HTMLInputElement | null>(null);
	let open = $state(false);
	let query = $state('');
	let focused = $state(-1);
	let position = $state<Record<string, string>>({});

	const choices = $derived<Choice[]>([
		...(empty !== undefined ? [{ value: '', label: empty, blank: true }] : []),
		...options.map((option) => ({ ...option, blank: false }))
	]);
	const selected = $derived(choices.find((choice) => choice.value === value) ?? null);
	const searchable = $derived(!!onsearch || choices.length > SEARCH_FROM);
	const shown = $derived(filter(searchable ? query : ''));
	const boxSize = $derived(size === 'sm' ? 'px-2.5 py-1.5 text-xs' : 'h-10 px-3 text-sm');

	// Case and accents do not matter ("agung" finds "Águng").
	function plain(text: string): string {
		return text.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
	}

	// Labels that start with the query come first, the ones merely containing it follow; the empty choice only shows when not searching.
	function filter(text: string): Choice[] {
		if (onsearch) return choices.filter((choice) => !choice.blank);
		const needle = plain(text.trim());
		if (needle === '') return choices;
		const starts: Choice[] = [];
		const contains: Choice[] = [];
		for (const choice of choices) {
			if (choice.blank) continue;
			const label = plain(choice.label);
			if (label.startsWith(needle)) starts.push(choice);
			else if (label.includes(needle)) contains.push(choice);
		}
		return [...starts, ...contains];
	}

	function show(): void {
		if (disabled || !button) return;
		const box = button.getBoundingClientRect();
		const ideal = Math.min(320, choices.length * 34 + 12 + (searchable ? 48 : 0));
		const below = window.innerHeight - box.bottom - 12;
		const above = box.top - 12;
		const up = below < ideal && above > below;
		const height = Math.max(120, Math.min(320, up ? above : below));
		position = {
			left: `${box.left}px`,
			width: `${Math.max(box.width, 160)}px`,
			'max-height': `${height}px`,
			...(up ? { bottom: `${window.innerHeight - box.top + 4}px` } : { top: `${box.bottom + 4}px` })
		};
		query = '';
		open = true;
		onsearch?.('');
		focused = Math.max(0, shown.findIndex((choice) => choice.value === value));
		void tick().then(() => {
			scrollToFocused();
			if (searchable) search?.focus({ preventScroll: true });
		});
	}

	function hide(): void {
		open = false;
		focused = -1;
		query = '';
	}

	function scrollToFocused(): void {
		list?.querySelector('[data-focused="true"]')?.scrollIntoView({ block: 'nearest' });
	}

	function nearEnd(): void {
		const box = list?.querySelector('ul');
		if (onmore && box && box.scrollTop + box.clientHeight >= box.scrollHeight - MORE_BEFORE_PX) onmore();
	}

	// Daftar yang belum cukup panjang untuk digulir langsung meminta halaman berikutnya.
	$effect(() => {
		if (!open || !onmore || shown.length === 0) return;
		void tick().then(nearEnd);
	});

	function type(event: Event): void {
		query = (event.currentTarget as HTMLInputElement).value;
		onsearch?.(query);
		focused = filter(query).length > 0 ? 0 : -1;
		void tick().then(() => list?.querySelector('ul')?.scrollTo({ top: 0 }));
	}

	function pick(choice: Choice): void {
		hide();
		button?.focus();
		if (choice.value === value) return;
		value = choice.value;
		onchange?.(choice.value);
	}

	function move(step: 1 | -1): void {
		const next = focused + step;
		if (next < 0 || next >= shown.length) return;
		focused = next;
		void tick().then(scrollToFocused);
	}

	function keydown(event: KeyboardEvent): void {
		if (!open) {
			if (['ArrowDown', 'ArrowUp', controlText.enterKey, ' '].includes(event.key)) {
				event.preventDefault();
				show();
			} else if (searchable && event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
				// Typing on the closed box opens it and starts the search.
				event.preventDefault();
				show();
				query = event.key;
				onsearch?.(query);
				focused = filter(query).length > 0 ? 0 : -1;
			}
			return;
		}
		// A space in the search box is a letter ("Putri Uci"), not a pick.
		if (event.target === search && event.key === ' ') return;
		if (event.key === 'Escape') {
			event.preventDefault();
			event.stopPropagation();
			hide();
		} else if (event.key === 'ArrowDown') {
			event.preventDefault();
			move(1);
		} else if (event.key === 'ArrowUp') {
			event.preventDefault();
			move(-1);
		} else if (event.key === 'Tab') {
			hide();
		} else if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			const choice = shown[focused];
			if (choice) pick(choice);
		}
	}

	// The list sits at a fixed position so a scrolling parent cannot clip it; a click outside, a scroll or a resize therefore closes it.
	$effect(() => {
		if (!open) return;
		const outside = (event: PointerEvent) => {
			const target = event.target as Node;
			if (button?.contains(target) || list?.contains(target)) return;
			hide();
		};
		// The phone keyboard that comes up for the search box resizes and shifts the screen; that is no reason to close.
		const typing = () => !!search && document.activeElement === search;
		const scroll = (event: Event) => {
			if (list && event.target instanceof Node && list.contains(event.target)) return;
			if (!typing()) hide();
		};
		const resize = () => {
			if (!typing()) hide();
		};
		document.addEventListener('pointerdown', outside);
		window.addEventListener('scroll', scroll, true);
		window.addEventListener('resize', resize);
		return () => {
			document.removeEventListener('pointerdown', outside);
			window.removeEventListener('scroll', scroll, true);
			window.removeEventListener('resize', resize);
		};
	});
</script>

<div class="relative max-w-full {className}">
	<button
		bind:this={button}
		{id}
		type="button"
		{disabled}
		onclick={() => (open ? hide() : show())}
		onkeydown={keydown}
		aria-haspopup="listbox"
		aria-expanded={open}
		aria-label={ariaLabel}
		aria-describedby={describedby}
		data-invalid={invalid ? 'true' : undefined}
		class="flex w-full items-center gap-2 rounded-md border bg-white text-left text-slate-800 transition-colors focus:outline-none focus:ring-2 focus:ring-brand-line disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500 {boxSize} {invalid
			? 'border-danger-500 focus:border-danger-500'
			: open
				? 'border-brand-focus'
				: 'border-slate-200 hover:border-slate-300 focus:border-brand-focus'}"
	>
		<!-- Every label is stacked invisibly in the same cell, so the box is as wide as the longest choice and does not jump when the choice changes. -->
		<span class="grid min-w-0 flex-1">
			{#each choices as choice (choice.value)}
				<span class="invisible col-start-1 row-start-1 truncate" aria-hidden="true">{choice.label}</span>
			{/each}
			<span class="col-start-1 row-start-1 truncate {selected && !selected.blank ? '' : 'text-slate-500'}">{selected?.label ?? ''}</span>
		</span>
		<i class="ti ti-chevron-down shrink-0 text-slate-400 transition-transform {open ? 'rotate-180' : ''}" aria-hidden="true"></i>
	</button>

	{#if open}
		<div bind:this={list} use:dynamicStyle={position} class="fixed z-70 flex flex-col overflow-hidden rounded-lg border border-slate-200 bg-white shadow-xl">
			{#if searchable}
				<div class="shrink-0 border-b border-slate-100 p-1.5">
					<input
						bind:this={search}
						type="text"
						value={query}
						oninput={type}
						onkeydown={keydown}
						placeholder={controlText.typeToSearch}
						aria-label={controlText.searchOptions}
						autocomplete="off"
						autocapitalize="off"
						spellcheck="false"
						class="w-full rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-base text-slate-700 placeholder:text-slate-500 focus:border-brand focus:bg-white focus:outline-none tablet:text-xs"
					/>
				</div>
			{/if}
			<div class="relative flex min-h-0 flex-1 flex-col">
			<ul role="listbox" aria-label={ariaLabel} aria-busy={searching || loadingMore} onscroll={nearEnd} class="min-h-0 flex-1 overflow-y-auto p-1">
				{#if searching}
					{#each { length: SEARCH_SKELETON_ROWS } as _, line (line)}
						<li role="presentation" class="px-1 py-1"><Skeleton class="h-6 w-full" /></li>
					{/each}
				{:else}
				{#each shown as choice, index (choice.value)}
					<li role="option" aria-selected={choice.value === value}>
						<button
							type="button"
							data-focused={index === focused}
							onclick={() => pick(choice)}
							onmouseenter={() => (focused = index)}
							class="flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-left text-xs {index === focused ? 'bg-brand-soft text-brand-deep' : 'text-slate-700'} {choice.value === value ? 'font-semibold' : ''}"
						>
							<span class="min-w-0 flex-1 wrap-break-word {choice.blank ? 'text-slate-500' : ''}">{choice.label}</span>
							{#if choice.value === value}<i class="ti ti-check shrink-0 text-brand" aria-hidden="true"></i>{/if}
						</button>
					</li>
				{:else}
					<li role="presentation" class="px-2.5 py-3 text-center text-xs text-slate-500">{format(controlText.noOptionMatches, { term: query })}</li>
				{/each}
				{/if}
				{#if loadingMore}
					{#each { length: MORE_SKELETON_ROWS } as _, line (line)}
						<li role="presentation" class="px-1 py-1"><Skeleton class="h-6 w-full" /></li>
					{/each}
				{/if}
			</ul>
			{#if searching || loadingMore}<ProgressLine />{/if}
			</div>
		</div>
	{/if}
</div>
