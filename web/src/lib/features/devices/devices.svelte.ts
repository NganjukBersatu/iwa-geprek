import { api } from '$lib/api';
import type { Device } from '$lib/api/types';
import { Filters } from '$lib/components/filter/filters.svelte';
import { BRANCH_SORT } from '$lib/components/table/branch-column';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { ManageState } from '../manage/manage.svelte';
import { deviceColumns } from './columns';
import { branchList } from '$lib/stores/branch';
import { termText } from '$lib/text/terms';

export class DevicesState extends ManageState<Device> {
	override readonly tables = ['devices', 'device_links', 'device_stations', 'device_station_prints', 'stations'];
	readonly sort = new ListSort('perangkat', [...sortKeys(deviceColumns), BRANCH_SORT], () => void this.queryChanged());

	readonly filters = new Filters([{ kind: 'select', key: 'cabang', label: termText.branch, options: [] }]);

	outlets = $state<{ id: string; name: string }[]>([]);

	get query(): string | null {
		return this.filters.get('cabang');
	}

	protected async fetch(): Promise<void> {
		this.outlets = await branchList();
		this.filters.setOptions('cabang', this.outlets.map((outlet) => ({ value: outlet.id, label: outlet.name })));
		this.items = await api.devices.list(this.sort.param);
		this.total = this.items.length;
	}

	protected label(device: Device): string {
		return device.name;
	}
}
