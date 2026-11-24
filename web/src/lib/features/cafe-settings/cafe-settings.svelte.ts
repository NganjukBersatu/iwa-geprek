import { api } from '$lib/api';
import type { CafeSettings, CafeSettingsInput } from '$lib/api/types';
import { Filters } from '$lib/components/filter/filters.svelte';
import { cafeSettingsText } from '$lib/text/cafe-settings';
import { ManageState } from '../manage/manage.svelte';

const NOTICE_MILLISECONDS = 4000;

export type SettingsRow = CafeSettings & { id: string };

/** Pengaturan satu cabang (struk serta harga dan margin) di halaman detail cabang; cabangnya mengikuti cabang yang dibuka. */
export class CafeSettingsState extends ManageState<SettingsRow> {
	override readonly tables = ['cafe_settings'];
	readonly filters = new Filters([{ kind: 'select', key: 'cabang', label: cafeSettingsText.branchFilter, options: [] }]);

	notice = $state('');
	private noticeTimer: ReturnType<typeof setTimeout> | undefined;

	get query(): string | null {
		return this.filters.get('cabang');
	}

	get settings(): SettingsRow | null {
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
		const settings = await api.cafeSettings.read();
		this.items = [{ ...settings, id: settings.outlet_id }];
		this.total = 1;
	}

	protected label(row: SettingsRow): string {
		return row.name || row.outlet_id;
	}

	/** Hanya kolom bagian yang disimpan yang dikirim, jadi menyimpan struk tidak mengirim ulang harga, begitu juga sebaliknya. */
	async save(values: CafeSettingsInput, saved: string, failed: string): Promise<void> {
		const done = await this.attempt(async () => {
			const settings = await api.cafeSettings.update(values);
			this.items = [{ ...settings, id: settings.outlet_id }];
		}, failed);
		if (!done) return;
		this.notice = saved;
		clearTimeout(this.noticeTimer);
		this.noticeTimer = setTimeout(() => (this.notice = ''), NOTICE_MILLISECONDS);
	}
}
