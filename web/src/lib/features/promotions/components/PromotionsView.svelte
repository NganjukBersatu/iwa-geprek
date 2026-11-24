<script lang="ts">
	import { announcementNewPath, promoNewPath } from '$lib/nav/pages';
	import { goto } from '$app/navigation';
	import { announcementPath, promoPath } from '$lib/nav/pages';
	import type { Promo } from '$lib/api/types';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import AddButton from '$lib/components/button/AddButton.svelte';
	import BulkEntryDialog from '$lib/components/dialog/BulkEntryDialog.svelte';
	import type { Field } from '$lib/components/form/types';
	import BulkActions from '$lib/components/table/BulkActions.svelte';
	import Pager from '$lib/components/pager/Pager.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import type { PromotionsState } from '../promotions.svelte';
	import { KIND_LABELS, STATUS_LABELS, STATUS_TONES } from '../labels';
	import { announcementColumns, promoColumns } from '../columns';
	import { termText } from '$lib/text/terms';
	import { promotionText } from '$lib/text/promotions';

	let { promotions }: { promotions: PromotionsState } = $props();

	const status = (value: string) => ({ label: STATUS_LABELS[value] ?? value, tone: STATUS_TONES[value as keyof typeof STATUS_TONES] ?? 'neutral' });


	const activationOptions = [
		{ value: 'otomatis', label: promotionText.automaticAtCashier },
		{ value: 'manual', label: promotionText.chosenByCashier }
	];

	const entryColumns: Field[] = [
		{ key: 'name', label: promotionText.promoName, required: true },
		{ key: 'kind', label: promotionText.appliesTo, kind: 'select', required: true, options: [{ value: 'basic', label: KIND_LABELS.basic ?? promotionText.wholeOrder }, { value: 'total', label: KIND_LABELS.total ?? promotionText.minimumPurchase }] },
		{ key: 'discount_type', label: promotionText.discountType, kind: 'select', required: true, options: [{ value: 'persen', label: promotionText.percent }, { value: 'nominal', label: promotionText.amount }] },
		{ key: 'value', label: termText.discount, kind: 'number', required: true },
		{ key: 'minimum_spend', label: promotionText.minimumPurchaseAmount, kind: 'number' },
		{ key: 'activation', label: promotionText.activation, kind: 'select', options: activationOptions },
		{ key: 'starts_on', label: promotionText.from, kind: 'date', required: true },
		{ key: 'ends_on', label: promotionText.until, kind: 'date', required: true },
		{ key: 'description', label: termText.description }
	];

	const promoChangeFields: Field[] = [
		{ key: 'is_active', label: termText.status, kind: 'toggle', yes: termText.active, no: termText.inactive },
		{ key: 'activation', label: promotionText.activation, kind: 'select', options: activationOptions },
		{ key: 'ends_on', label: promotionText.validUntil, kind: 'date' }
	];

	const announcementChangeFields: Field[] = [
		{ key: 'is_active', label: termText.status, kind: 'toggle', yes: termText.active, no: termText.inactive },
		{ key: 'ends_on', label: promotionText.validUntil, kind: 'date' }
	];

</script>

{#if promotions.actionError}
	<Banner tone="danger" icon="alert-circle">{promotions.actionError}</Banner>
{/if}

<Card flush>
	<CardHeader divided title={promotionText.promosTitle} description={promotionText.promosDescription}>
		{#snippet actions()}
			<AddButton label={promotionText.addPromo} onone={() => void goto(promoNewPath())} onmany={() => (promotions.entryOpen = true)} />
		{/snippet}
	</CardHeader>
	{#if promotions.total === 0}
		<Notice text={promotionText.noPromos} />
	{:else}
		<DataTable sort={promotions.sort} columns={promoColumns} rows={promotions.items} rowKey={(row) => row.id} loading={promotions.loading} selection={promotions.selection} trailing="potongan" onopen={(row) => void goto(promoPath(row.id))}>
			{#snippet first(row)}
				{@const shown = status(row.status)}
				<span class="inline-flex items-center gap-2">
					<span>{row.name}</span>
					<Badge tone={shown.tone}>{shown.label}</Badge>
				</span>
			{/snippet}
		</DataTable>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={promotions.page} total={promotions.total} unit="promo" disabled={promotions.loading} onchange={(page) => promotions.setPage(page)} />
		</div>
	{/if}
</Card>

<Card flush>
	<CardHeader divided title={promotionText.announcementsTitle} description={promotionText.announcementsDescription}>
		{#snippet actions()}
			<Button label={promotionText.addAnnouncement} icon="plus" variant="primary" compact onclick={() => void goto(announcementNewPath())} />
		{/snippet}
	</CardHeader>
	{#if promotions.announcementTotal === 0}
		<Notice text={promotionText.noAnnouncements} />
	{:else}
		<DataTable sort={promotions.announcementSort} columns={announcementColumns} rows={promotions.announcements} rowKey={(row) => row.id} selection={promotions.announcementSelection} onopen={(row) => void goto(announcementPath(row.id))}>
			{#snippet first(row)}
				{@const shown = status(row.status)}
				<span class="inline-flex items-center gap-2">
					<span>{row.title}</span>
					<Badge tone={shown.tone}>{shown.label}</Badge>
					{#if row.image_url}<i class="ti ti-photo text-slate-500" aria-label={promotionText.withImage}></i>{/if}
				</span>
			{/snippet}
		</DataTable>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={promotions.announcementPage} total={promotions.announcementTotal} unit="promosi" disabled={promotions.loading} onchange={(page) => promotions.setAnnouncementPage(page)} />
		</div>
	{/if}
</Card>

<BulkActions
	selection={promotions.selection}
	noun="promo"
	bind:removing={promotions.bulkRemovePromos}
	bind:changing={promotions.changePromosOpen}
	fields={promoChangeFields}
	onchange={(changes) => void promotions.changePromos(changes)}
	busy={promotions.busy}
	error={promotions.actionError}
	onremove={() => void promotions.removePromos()}
	oncancel={() => promotions.closeDialogs()}
>
	{promotionText.promoBulkRemoveNote}
</BulkActions>

<BulkActions
	selection={promotions.announcementSelection}
	noun="promosi"
	bind:removing={promotions.bulkRemoveAnnouncements}
	bind:changing={promotions.changeAnnouncementsOpen}
	fields={announcementChangeFields}
	onchange={(changes) => void promotions.changeAnnouncements(changes)}
	busy={promotions.busy}
	error={promotions.actionError}
	onremove={() => void promotions.removeAnnouncements()}
	oncancel={() => promotions.closeDialogs()}
>
	{promotionText.announcementRemoveNote}
</BulkActions>

{#if promotions.entryOpen}
	<BulkEntryDialog
		title={promotionText.bulkTitle}
		hint={promotionText.bulkHint}
		columns={entryColumns}
		submit={(rows) => promotions.createMany(rows)}
		submitLabel="Simpan semua promo"
		onclose={() => promotions.closeDialogs()}
	/>
{/if}
