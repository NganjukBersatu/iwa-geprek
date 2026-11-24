import type { MoneyAction, MoneySubject } from '$lib/api/types';
import { termText } from '$lib/text/terms';
import { moneyChangeText } from '$lib/text/money-changes';

export const SUBJECT_LABELS: Record<MoneySubject, string> = {
	order: termText.transaction,
	expense: termText.expense,
	overpayment: moneyChangeText.overpayment,
	session: termText.cashierSession
};

export const ACTION_LABELS: Record<MoneyAction, string> = {
	late: moneyChangeText.recordedLate,
	update: moneyChangeText.changed,
	void: moneyChangeText.voided,
	unvoid: moneyChangeText.voidCancelled,
	delete: moneyChangeText.removed,
	move_out: moneyChangeText.movedAway,
	move_in: moneyChangeText.movedIn
};

/** The money fields the database names when it records a change. */
const FIELD_LABELS: Record<string, string> = {
	total: 'total',
	void: 'void',
	payment_method: 'metode pembayaran',
	outlet: 'cabang',
	business_day: 'hari',
	amount: 'jumlah',
	fund_source: 'sumber dana',
	opening_cash: 'modal awal',
	actual_cash: 'uang aktual',
	difference: 'selisih'
};

export function fieldsText(fields: string[]): string {
	return fields.map((field) => FIELD_LABELS[field] ?? field).join(', ');
}

export const SYSTEM_ACTOR = moneyChangeText.systemOrLegacy;
