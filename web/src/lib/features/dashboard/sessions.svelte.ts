import { userMessage } from '$lib/api/user-message';
import { api } from '$lib/api';
import type { SessionRow as ApiSessionRow } from '$lib/api/types';
import type { DateRange } from '$lib/date/range';
import { ListSort } from '$lib/components/table/list-sort.svelte';
import { SESSION_SORTS } from './columns';
import { dashboardCardText } from '$lib/text/dashboard-cards';

const MAX_SESSIONS = 40;

export type SessionRow = {
	id: string;
	cashier: string;
	start: string;
	end: string | null;
	income: number;
	expense: number;
};

export type Transaction = {
	time: string;
	kind: 'income' | 'expense';
	description: string;
	amount: string;
	qty?: number;
	/** The order behind an income line, so the line opens it. */
	orderId?: string;
};

function toRow(session: ApiSessionRow): SessionRow {
	return {
		id: session.id,
		cashier: session.cashier_username,
		start: session.opened_at,
		end: session.closed_at,
		income: Number(session.revenue),
		expense: Number(session.expense)
	};
}

export class SessionsState {
	private range: DateRange | null = null;
	readonly sort = new ListSort('dasbor-sesi', SESSION_SORTS, () => this.range && void this.load(this.range, true));
	rows = $state<SessionRow[]>([]);
	omitted = $state(0);
	openId = $state<string | null>(null);
	details = $state<Record<string, Transaction[]>>({});
	loadingId = $state<string | null>(null);
	detailError = $state('');

	async load(range: DateRange, quiet = false): Promise<void> {
		this.range = range;
		const list = await api.sessions.list({ start: range.from, end: range.to, limit: MAX_SESSIONS, sort: this.sort.param });
		this.omitted = Math.max(0, list.total - list.items.length);
		this.rows = list.items.map(toRow);
		// A quiet reload keeps the row someone has opened, with the lines already read.
		if (quiet && this.rows.some((row) => row.id === this.openId)) return;
		this.details = {};
		this.openId = null;
		this.detailError = '';
	}

	clear(): void {
		this.range = null;
		this.rows = [];
		this.omitted = 0;
		this.openId = null;
		this.details = {};
	}

	/** The session whose lines are shown; its lines are fetched once and kept. */
	async unfold(id: string): Promise<void> {
		this.openId = id;
		await this.loadDetail(id);
	}

	private async loadDetail(id: string): Promise<void> {
		if (this.details[id]) return;
		this.loadingId = id;
		this.detailError = '';
		try {
			const result = await api.sessions.lines(id);
			this.details[id] = result.lines.map((line) => ({
				time: line.at,
				kind: line.kind,
				description: line.description,
				amount: line.amount,
				qty: line.quantity ?? undefined,
				orderId: line.order_id ?? undefined
			}));
		} catch (error) {
			if (this.openId === id) this.detailError = userMessage(error, dashboardCardText.sessionDetailsLoadFailed);
		} finally {
			if (this.loadingId === id) this.loadingId = null;
		}
	}
}
