import { userMessage } from '$lib/api/user-message';
import { api } from '$lib/api';
import type { ManagedStation, StationOption, StationSetup } from '$lib/api/types';
import { access } from '$lib/auth/access.svelte';
import { Filters } from '$lib/components/filter/filters.svelte';
import { STATION_TABLES } from '$lib/live/tables';
import { PAGES } from '$lib/nav/pages';
import { branchList } from '$lib/stores/branch';
import { stationText } from '$lib/text/stations';
import { termText } from '$lib/text/terms';

/** Pilihan stasiun untuk kategori yang tidak dibuat di Dapur atau Bar. */
export const DIRECT = 'direct-delivery';
export const DIRECT_LABEL = stationText.directDelivery;

/** Satu baris kartu Kategori menu ke stasiun: baris semua cabang (outletId null) atau baris cabang yang berbeda. */
export type CategoryRow = {
	id: string;
	categoryId: string;
	categoryName: string;
	first: boolean;
	stationId: string | null;
	outletId: string | null;
	outletName: string;
};

/** Isian dialog Tambah cabang dan Ubah. */
export type RouteForm = { mode: 'add' | 'edit'; categoryId: string; outletId: string | null; stationId: string };

export class SetupState {
	readonly tables = [...STATION_TABLES, 'category_stations', 'category_branch_stations', 'categories', 'outlets', 'devices', 'device_stations', 'device_station_prints'];
	readonly filters = new Filters([{ kind: 'select', key: 'cabang', label: termText.branch, options: [] }]);

	loading = $state(true);
	error = $state('');
	data = $state<StationSetup | null>(null);
	outlets = $state<{ id: string; name: string }[]>([]);
	busy = $state(false);
	actionError = $state('');
	form = $state<RouteForm | null>(null);
	removing = $state<CategoryRow | null>(null);
	/** Tablet pemegang tiap stasiun di cabang terpilih; null bila semua cabang atau akun tanpa akses perangkat cabang. */
	coverage = $state<StationOption[] | null>(null);
	private token = 0;

	get branch(): string | null {
		return this.filters.get('cabang');
	}

	get rows(): CategoryRow[] {
		return (this.data?.categories ?? []).flatMap((category) => [
			{ id: category.id, categoryId: category.id, categoryName: category.name, first: true, stationId: category.station_id, outletId: null, outletName: '' },
			...category.branches.map((branch) => ({
				id: `${category.id}:${branch.outlet_id}`,
				categoryId: category.id,
				categoryName: category.name,
				first: false,
				stationId: branch.station_id,
				outletId: branch.outlet_id,
				outletName: branch.outlet_name
			}))
		]);
	}

	/** Nama tablet pemegang stasiun; null bila keadaannya tidak diketahui. */
	holders(station: ManagedStation): string[] | null {
		if (this.coverage === null) return null;
		return this.coverage.find((cover) => cover.id === station.id)?.device_names ?? [];
	}

	get branchName(): string {
		return this.outlets.find((outlet) => outlet.id === this.branch)?.name ?? '';
	}

	stationName(stationId: string | null): string {
		if (stationId === null) return DIRECT_LABEL;
		return this.data?.stations.find((station) => station.id === stationId)?.name ?? DIRECT_LABEL;
	}

	/** Cabang yang belum punya baris sendiri untuk kategori ini; cabang yang sedang diubah tetap ada. */
	branchesFor(categoryId: string, keep: string | null): { value: string; label: string }[] {
		const taken = new Set(this.data?.categories.find((category) => category.id === categoryId)?.branches.map((branch) => branch.outlet_id) ?? []);
		return this.outlets.filter((outlet) => outlet.id === keep || !taken.has(outlet.id)).map((outlet) => ({ value: outlet.id, label: outlet.name }));
	}

	async load(quiet = false): Promise<void> {
		const token = ++this.token;
		if (!quiet) {
			this.loading = true;
			this.error = '';
		}
		try {
			const branch = this.branch;
			const [data, outlets, coverage] = await Promise.all([
				api.stations.setup({ outlet_id: branch }),
				branchList(),
				branch !== null && access.opens(PAGES.devices.screen) ? api.devices.stations(branch) : Promise.resolve(null)
			]);
			if (token !== this.token) return;
			this.data = data;
			this.coverage = coverage;
			this.outlets = outlets.map((outlet) => ({ id: outlet.id, name: outlet.name }));
		} catch (error) {
			if (token !== this.token || quiet) return;
			this.data = null;
			this.error = userMessage(error, stationText.setupLoadFailed);
		} finally {
			if (token === this.token) this.loading = false;
		}
	}

	openAdd(): void {
		const first = this.data?.categories.at(0);
		this.actionError = '';
		this.form = { mode: 'add', categoryId: first?.id ?? '', outletId: null, stationId: DIRECT };
	}

	openEdit(row: CategoryRow): void {
		this.actionError = '';
		this.form = { mode: 'edit', categoryId: row.categoryId, outletId: row.outletId, stationId: row.stationId ?? DIRECT };
	}

	askRemove(row: CategoryRow): void {
		this.actionError = '';
		this.removing = row;
	}

	closeDialogs(): void {
		if (this.busy) return;
		this.form = null;
		this.removing = null;
		this.actionError = '';
	}

	async saveForm(): Promise<void> {
		const form = this.form;
		if (!form) return;
		if (form.mode === 'add' && !form.outletId) {
			this.actionError = stationText.chooseBranchError;
			return;
		}
		const stationId = form.stationId === DIRECT ? null : form.stationId;
		const outletId = form.outletId;
		const done = await this.act(() =>
			outletId === null
				? api.stations.setCategory(form.categoryId, { station_id: stationId })
				: api.stations.setCategoryBranch(form.categoryId, outletId, { follows_default: false, station_id: stationId })
		);
		if (done) this.form = null;
	}

	async remove(): Promise<void> {
		const row = this.removing;
		if (!row?.outletId) return;
		const outletId = row.outletId;
		const done = await this.act(() => api.stations.setCategoryBranch(row.categoryId, outletId, { follows_default: true }));
		if (done) this.removing = null;
	}

	private async act(work: () => Promise<void>): Promise<boolean> {
		if (this.busy) return false;
		this.busy = true;
		this.actionError = '';
		try {
			await work();
			await this.load(true);
			return true;
		} catch (error) {
			this.actionError = userMessage(error, stationText.changesSaveFailed);
			return false;
		} finally {
			this.busy = false;
		}
	}
}
