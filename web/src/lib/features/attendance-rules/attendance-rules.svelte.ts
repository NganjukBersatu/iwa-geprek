import { toast } from '$lib/components/feedback/toast.svelte';
import { api } from '$lib/api';
import type { AttendanceRules } from '$lib/api/types';
import { Filters } from '$lib/components/filter/filters.svelte';
import { attendanceRulesText } from '$lib/text/attendance-rules';
import { termText } from '$lib/text/terms';
import { ManageState } from '../manage/manage.svelte';

export type RulesRow = AttendanceRules & { id: string };

/** Aturan absensi satu cabang di halaman detail cabang; cabangnya mengikuti cabang yang dibuka. */
export class AttendanceRulesState extends ManageState<RulesRow> {
	override readonly tables = ['cafe_settings'];
	readonly filters = new Filters([{ kind: 'select', key: 'cabang', label: termText.branch, options: [] }]);

	get query(): string | null {
		return this.filters.get('cabang');
	}

	/** Aturan cabang yang dibuka; kosong sampai aturan cabang itu sendiri sudah tiba. */
	get rules(): RulesRow | null {
		const branch = this.query;
		const row = this.items[0];
		return branch && row?.id === branch ? row : null;
	}

	protected async fetch(): Promise<void> {
		if (!this.query) {
			this.items = [];
			this.total = 0;
			return;
		}
		const rules = await api.attendanceRules.read();
		this.items = [{ ...rules, id: rules.outlet_id }];
		this.total = 1;
	}

	protected label(row: RulesRow): string {
		return row.outlet_id;
	}

	async save(values: { late_tolerance_minutes: number; late_penalty_per_minute: number; auto_close_after_hours: number }): Promise<void> {
		const done = await this.attempt(async () => {
			const rules = await api.attendanceRules.update(values);
			this.items = [{ ...rules, id: rules.outlet_id }];
		}, attendanceRulesText.saveFailed);
		if (!done) return;
		toast.show(attendanceRulesText.saved);
	}
}
