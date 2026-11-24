<script lang="ts">
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { Promo, PromoMenu, PromoUpdate } from '$lib/api/types';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import FigureGrid from '$lib/components/card/FigureGrid.svelte';
	import { formatDate } from '$lib/date/range';
	import { scopeText } from '$lib/components/form/branch-prices.svelte';
	import { branches } from '$lib/stores/branch';
	import { EMPTY_VALUE, formatNumber, formatRupiah } from '$lib/format/currency';
	import { PAGES } from '$lib/nav/pages';
	import { recordText } from '$lib/text/record-detail';
	import RecordDetailView from '../../record-detail/components/RecordDetailView.svelte';
	import { RecordDetailState } from '../../record-detail/record-detail.svelte';
	import { KIND_LABELS, STATUS_LABELS, STATUS_TONES } from '../labels';
	import PromoForm from './PromoForm.svelte';
	import { termText } from '$lib/text/terms';
	import { promotionText } from '$lib/text/promotions';

	let { id }: { id: string } = $props();

	const detail = new RecordDetailState<Promo, PromoUpdate, PromoMenu[]>(untrack(() => id), {
		load: (promoId) => api.promotions.promo(promoId),
		context: () => api.promotions.menus(),
		update: (promo, body) => api.promotions.updatePromo(promo.id, body),
		remove: (promo) => api.promotions.removePromo(promo.id),
		name: (promo) => promo.name,
		text: recordText('promo', PAGES.promotions.label)
	});

	const cut = (promo: Promo) => (promo.discount_type === 'persen' ? `${formatNumber(promo.value)}%` : formatRupiah(promo.value));
</script>

<RecordDetailView {detail} back={PAGES.promotions} trail={(promo) => [{ label: PAGES.promotions.label, href: PAGES.promotions.path }, { label: promo.name }]} tables={['promos', 'menu_items']} title={(promo) => promo.name} description={(promo) => promo.description ?? ''}>
	{#snippet badge(promo)}
		<Badge tone={STATUS_TONES[promo.status]}>{STATUS_LABELS[promo.status]}</Badge>
	{/snippet}
	{#snippet extraActions(promo)}
		<Button
			label={promo.is_active ? promotionText.deactivate : promotionText.activate}
			icon={promo.is_active ? 'player-pause' : 'player-play'}
			variant="tertiary"
			disabled={detail.busy}
			onclick={() => void detail.change((current) => api.promotions.updatePromo(current.id, { is_active: !current.is_active }), promotionText.promoStatusChangeFailed)}
		/>
	{/snippet}
	{#snippet body(promo)}
		<Card flush>
			<div class="p-4 tablet:p-5">
				<FigureGrid
					label={promotionText.promoSummary}
					figures={[
						{ label: termText.name, value: promo.name },
						{ label: termText.status, value: STATUS_LABELS[promo.status] ?? promo.status },
						{ label: promotionText.appliesTo, value: KIND_LABELS[promo.kind] ?? promo.kind },
						{ label: termText.branch, value: scopeText(promo.outlet_id, $branches) },
						{ label: promotionText.activation, value: promo.activation === 'manual' ? promotionText.chosenByCashier : promotionText.automatic },
						{ label: promotionText.cutAmount, value: cut(promo) },
						{ label: promotionText.minimumSpend, value: promo.minimum_spend ? formatRupiah(promo.minimum_spend) : EMPTY_VALUE },
						{ label: promotionText.from, value: formatDate(promo.starts_on) },
						{ label: promotionText.until, value: formatDate(promo.ends_on) }
					]}
				/>
			</div>
			<section class="flex flex-col gap-2 border-t border-slate-100 p-4 tablet:p-5">
				<h3 class="text-sm font-semibold text-slate-800">{termText.menu}</h3>
				{#if promo.kind === 'produk'}
					{#if promo.product_names.length > 0}
						<ul class="flex flex-wrap gap-2">
							{#each promo.product_names as menuName (menuName)}<li><Badge tone="brand">{menuName}</Badge></li>{/each}
						</ul>
					{:else}
						<p class="text-xs text-slate-500">{promotionText.chosenMenuRemoved}</p>
					{/if}
				{:else}
					<p class="text-xs text-slate-500">{promotionText.notLimitedToMenus}</p>
				{/if}
			</section>
		</Card>
	{/snippet}
	{#snippet form(props)}
		<PromoForm promo={props.record} menus={props.context ?? []} busy={props.busy} error={props.error} fieldErrors={props.fieldErrors} onsave={(body) => props.onsave(body as PromoUpdate)} onclose={props.onclose} />
	{/snippet}
	{#snippet removeNote()}
		{promotionText.promoRemoveNote}
	{/snippet}
</RecordDetailView>
