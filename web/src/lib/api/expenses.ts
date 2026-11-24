import { bulkApi } from './bulk';
import { del, inBranch, patch, post, request, toQuery, upload, type SortParam } from './http';
import type { BuyerChoice, Expense, ExpenseCreate, ExpensePage, ExpenseReceipt, ExpenseUpdate, IngredientChoice, ReceiptReading, SessionChoicePage } from './types';

const BASE = '/web/management/expenses';
// Satu halaman pilihan; halaman berikutnya diminta saat daftar digulir.
export const CHOICE_SIZE = 50;

export type ExpenseParams = SortParam & { start?: string; end?: string; fund_source?: string; session_id?: string; search?: string; page?: number; size?: number };

export type SessionChoiceParams = { start?: string; end?: string; search?: string; size?: number; outlet_id?: string; cursor?: string };

export const expensesApi = {
	list: (params: ExpenseParams): Promise<ExpensePage> => request(`${BASE}?${toQuery(params)}`),
	sessionChoices: (params: SessionChoiceParams): Promise<SessionChoicePage> => request(`${BASE}/sessions/page?${toQuery(params)}`),
	detail: (id: string): Promise<Expense> => request(`${BASE}/${id}`),
	create: (outletId: string, body: ExpenseCreate): Promise<Expense> => post(inBranch(BASE, outletId), body),
	update: (id: string, body: ExpenseUpdate): Promise<Expense> => patch(`${BASE}/${id}`, body),
	remove: (id: string): Promise<void> => del(`${BASE}/${id}`),
	uploadReceipt: (id: string, file: Blob): Promise<Expense> => upload(`${BASE}/${id}/receipt`, 'file', file),
	/** With a branch the lines are matched against its ingredients; without one they come back plain. */
	readReceipt: (file: Blob, outletId: string): Promise<ReceiptReading> =>
		upload(outletId ? inBranch(`${BASE}/receipts/read`, outletId) : `${BASE}/receipts/read`, 'file', file),
	ingredients: (outletId: string, search: string, page: number): Promise<IngredientChoice[]> =>
		request(inBranch(`${BASE}/ingredients?${toQuery({ search, page, size: CHOICE_SIZE })}`, outletId)),
	buyers: (search: string, page: number): Promise<BuyerChoice[]> => request(`${BASE}/buyers?${toQuery({ search, page, size: CHOICE_SIZE })}`),
	recordReceipt: (outletId: string, body: ExpenseReceipt, file: Blob | null): Promise<Expense[]> => {
		const form = new FormData();
		form.append('data', JSON.stringify(body));
		if (file) form.append('file', file);
		return request(inBranch(`${BASE}/receipts`, outletId), { method: 'POST', body: form });
	},
	bulk: bulkApi<ExpenseCreate, ExpenseUpdate>(BASE)
};
