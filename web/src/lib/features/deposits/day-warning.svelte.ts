import { api } from '$lib/api';
import type { DayKey, DayState } from '$lib/api/types';

type Asked = { days: DayKey[]; expense_ids: string[]; running_session: boolean };

type Check = { kind: 'idle' } | { kind: 'checking' } | { kind: 'ready'; days: DayState[] } | { kind: 'failed' };

/** What a change to money would touch on its days, read right before the person confirms it; the confirm waits for the answer. */
export class DayWarning {
	check = $state<Check>({ kind: 'idle' });
	private token = 0;

	get checking(): boolean {
		return this.check.kind === 'checking';
	}

	/** Days already handed over, the ones a change would make short or over. */
	get deposited(): DayState[] {
		return this.check.kind === 'ready' ? this.check.days.filter((day) => Number(day.deposited) > 0) : [];
	}

	/** Days whose session still runs, which a deposit would settle before their money is final. */
	get unfinished(): DayState[] {
		return this.check.kind === 'ready' ? this.check.days.filter((day) => day.unfinished) : [];
	}

	get failed(): boolean {
		return this.check.kind === 'failed';
	}

	read(keys: DayKey[]): Promise<void> {
		return this.ask({ days: keys, expense_ids: [], running_session: false });
	}

	/** The days of expenses picked across pages, which the screen does not hold. */
	readExpenses(ids: string[]): Promise<void> {
		return this.ask({ days: [], expense_ids: ids, running_session: false });
	}

	private async ask(asked: Asked): Promise<void> {
		const token = ++this.token;
		if (asked.days.length === 0 && asked.expense_ids.length === 0) {
			this.check = { kind: 'ready', days: [] };
			return;
		}
		this.check = { kind: 'checking' };
		try {
			const days = await api.deposits.dayStates(asked);
			if (token === this.token) this.check = { kind: 'ready', days };
		} catch {
			if (token === this.token) this.check = { kind: 'failed' };
		}
	}

	clear(): void {
		this.token++;
		this.check = { kind: 'idle' };
	}
}
