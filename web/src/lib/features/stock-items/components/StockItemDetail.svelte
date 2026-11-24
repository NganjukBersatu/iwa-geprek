<script lang="ts">
	import { termText } from '$lib/text/terms';
	import { onMount, untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { StockCard, StockCardUpdate, StockItem, StockSettings } from '$lib/api/types';
	import { userMessage } from '$lib/api/user-message';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import { toast } from '$lib/components/feedback/toast.svelte';
	import { pageSize } from '$lib/components/pager/size.svelte';
	import Pager from '$lib/components/pager/Pager.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
	import { EMPTY_VALUE, formatNumber, formatRupiah } from '$lib/format/currency';
	import { formatDateTime } from '$lib/format/datetime';
	import { live } from '$lib/live/live';
	import { STOCK_TABLES } from '$lib/live/tables';
	import { PAGES } from '$lib/nav/pages';
	import { recordText } from '$lib/text/record-detail';
	import RecordDetailView from '../../record-detail/components/RecordDetailView.svelte';
	import { RecordDetailState } from '../../record-detail/record-detail.svelte';
	import { cardColumns } from '../columns';
	import { STOCK_STATUS } from '../labels';
	import type { MovementMode } from '../stock-items.svelte';
	import StockCardEditDialog from './StockCardEditDialog.svelte';
	import StockItemForm from './StockItemForm.svelte';
	import StockMovementDialog from './StockMovementDialog.svelte';
	import { stockItemText } from '$lib/text/stock-items';
	import { format } from '$lib/text/format';
	import RichText from '$lib/components/text/RichText.svelte';

	type Unit = { id: string; name: string };

	let { id }: { id: string } = $props();

	const detail = new RecordDetailState<StockItem, StockSettings, Unit[]>(untrack(() => id), {
		load: (itemId) => api.stockItems.detail(itemId),
		context: async () => (await api.ingredients.options()).units,
		update: (item, body) => api.stockItems.settings(item.outlet_id, item.menu_item_id, body),
		remove: (item) => api.stockItems.remove(item.outlet_id, item.menu_item_id),
		name: (item) => item.menu_item_name,
		text: recordText('barang', PAGES.stockItems.label)
	});

	const cardSort = new ListSort('barang-stok-riwayat', sortKeys(cardColumns), () => void loadCards(1));

	let cards = $state<StockCard[]>([]);
	let cardTotal = $state(0);
	let cardPage = $state(1);
	let cardsLoading = $state(true);
	let cardsError = $state('');
	let movement = $state<MovementMode | null>(null);
	let editing = $state<StockCard | null>(null);
	let removing = $state<StockCard | null>(null);
	let busy = $state(false);
	let actionError = $state('');

	async function loadCards(page = cardPage): Promise<void> {
		const item = detail.record;
		if (!item) return;
		cardsLoading = true;
		try {
			const result = await api.stockItems.cards(item.outlet_id, item.menu_item_id, page, pageSize.value, cardSort.param);
			cards = result.items;
			cardTotal = result.total;
			cardPage = page;
			cardsError = '';
		} catch (error) {
			cardsError = userMessage(error, stockItemText.cardsLoadFailed);
		} finally {
			cardsLoading = false;
		}
	}

	// The history follows the item: it is read once the item is known, and again after any change to the stock.
	let loadedFor = '';
	$effect(() => {
		const item = detail.record;
		if (item && loadedFor !== item.id) {
			loadedFor = item.id;
			void loadCards(1);
		}
	});

	onMount(() => live.on(STOCK_TABLES, () => void loadCards()));

	async function attempt(work: () => Promise<unknown>, fallback: string): Promise<boolean> {
		busy = true;
		actionError = '';
		try {
			await work();
			return true;
		} catch (error) {
			actionError = userMessage(error, fallback);
			return false;
		} finally {
			busy = false;
		}
	}

	async function saveMovement(item: StockItem, mode: MovementMode, body: { qty: string; unit_price?: string | null; note: string | null }): Promise<void> {
		const done = await attempt(
			() => (mode === 'receive' ? api.stockItems.receive(item.outlet_id, { menu_item_id: item.menu_item_id, ...body }) : api.stockItems.adjust(item.outlet_id, { menu_item_id: item.menu_item_id, qty: body.qty, note: body.note ?? '' })),
			stockItemText.movementSaveFailed
		);
		if (!done) return;
		movement = null;
		toast.show(mode === 'receive' ? format(stockItemText.receiveRecorded, { name: item.menu_item_name }) : format(stockItemText.balanceAdjusted, { name: item.menu_item_name }));
		await Promise.all([detail.refresh(), loadCards(1)]);
	}

	async function saveCard(body: StockCardUpdate): Promise<void> {
		const card = editing;
		if (!card) return;
		if (!(await attempt(() => api.stockItems.updateCard(card.id, body), stockItemText.cardSaveFailed))) return;
		editing = null;
		toast.show(stockItemText.cardUpdated);
		await Promise.all([detail.refresh(), loadCards()]);
	}

	async function removeCard(): Promise<void> {
		const card = removing;
		if (!card) return;
		if (!(await attempt(() => api.stockItems.removeCard(card.id), stockItemText.cardRemoveFailed))) return;
		removing = null;
		toast.show(stockItemText.cardRemoved);
		await Promise.all([detail.refresh(), loadCards()]);
	}

	function closeDialogs(): void {
		movement = null;
		editing = null;
		removing = null;
		actionError = '';
	}

	const balance = (item: StockItem) => `${formatNumber(item.balance)} ${item.unit ?? ''}`.trim();
</script>

<RecordDetailView
	{detail}
	back={PAGES.stockItems}
	trail={(item) => [{ label: PAGES.stockItems.label, href: PAGES.stockItems.path }, { label: item.menu_item_name }]}
	tables={STOCK_TABLES}
	title={(item) => item.menu_item_name}
	description={(item) => format(stockItemText.stockItemSubtitle, { branch: item.outlet_name, balance: balance(item) })}
>
	{#snippet badge(item)}
		<Badge tone={STOCK_STATUS[item.status]?.tone ?? 'neutral'}>{STOCK_STATUS[item.status]?.label ?? item.status}</Badge>
	{/snippet}
	{#snippet extraActions()}
		<Button label={stockItemText.receive} icon="plus" variant="tertiary" onclick={() => (movement = 'receive')} />
		<Button label={stockItemText.adjust} icon="adjustments" variant="tertiary" onclick={() => (movement = 'adjust')} />
	{/snippet}
	{#snippet body(item)}
		<Card flush class="grid laptop:grid-cols-2">
			<div class="border-b border-slate-100 p-4 tablet:p-5 laptop:border-b-0 laptop:border-r">
				<FigureList
					title={termText.stock}
					figures={[
						{ label: termText.branch, value: item.outlet_name },
						{ label: stockItemText.balance, value: balance(item), emphasis: 'total' },
						{ label: stockItemText.averageCost, value: item.cost === null ? EMPTY_VALUE : formatRupiah(item.cost) },
						{ label: stockItemText.inventoryValue, value: item.inventory_value === null ? EMPTY_VALUE : formatRupiah(item.inventory_value) }
					]}
				/>
			</div>
			<div class="p-4 tablet:p-5">
				<FigureList
					title={stockItemText.settings}
					figures={[
						{ label: termText.unit, value: item.unit ?? termText.notSet },
						{ label: stockItemText.minimumLimit, value: `${formatNumber(item.minimum)} ${item.unit ?? ''}`.trim() },
						{ label: stockItemText.reduceOnSale, value: item.is_tracked ? termText.yes : termText.no }
					]}
				/>
			</div>
		</Card>

		<Card flush>
			<CardHeader divided title={stockItemText.cardsTitle} description={stockItemText.cardsDescription} />
			{#if cardsError}
				<Notice text={cardsError} />
			{:else if !cardsLoading && cards.length === 0}
				<Notice text={stockItemText.noCards} />
			{:else}
				<DataTable sort={cardSort} columns={cardColumns} rows={cards} rowKey={(row) => row.id} loading={cardsLoading} trailing="pencatat" onopen={(row) => !row.order_id && (editing = row)}>
					{#snippet first(row)}
						<span class="block">{formatDateTime(row.created_at)}</span>
						{#if row.note}<span class="block max-w-xs truncate text-xs font-normal text-slate-500">{row.note}</span>{/if}
					{/snippet}
					{#snippet cell(row, column)}
						{#if column.key === 'jenis'}
							<Badge tone={row.kind === 'masuk' ? 'success' : row.kind === 'keluar' ? 'neutral' : 'warning'}>{column.value(row)}</Badge>
						{:else}
							{column.value(row)}
						{/if}
					{/snippet}
				</DataTable>
				<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
					<Pager page={cardPage} total={cardTotal} unit="catatan" disabled={cardsLoading} onchange={(next) => void loadCards(next)} />
				</div>
			{/if}
		</Card>

		{#if movement}
			<StockMovementDialog {item} mode={movement} {busy} error={actionError} onsave={(payload) => void saveMovement(item, movement!, payload)} onclose={closeDialogs} />
		{/if}
		{#if editing}
			<StockCardEditDialog card={editing} {busy} error={actionError} onsave={(payload) => void saveCard(payload)} onremove={() => { removing = editing; editing = null; }} onclose={closeDialogs} />
		{/if}
		<ConfirmDialog
			open={removing !== null}
			title={stockItemText.removeCardTitle}
			confirmLabel="Hapus"
			danger
			{busy}
			error={actionError}
			onconfirm={() => void removeCard()}
			oncancel={closeDialogs}
		>
			{stockItemText.removeCardNote}
		</ConfirmDialog>
	{/snippet}
	{#snippet form(props)}
		<StockItemForm item={props.record} units={props.context ?? []} busy={props.busy} error={props.error} fieldErrors={props.fieldErrors} onsave={props.onsave} onclose={props.onclose} />
	{/snippet}
	{#snippet removeNote(item)}
		<RichText template={stockItemText.stockItemRemoveNote} values={{ name: item.menu_item_name }} />
	{/snippet}
</RecordDetailView>
