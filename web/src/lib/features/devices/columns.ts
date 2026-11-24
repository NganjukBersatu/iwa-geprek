import type { Device } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE } from '$lib/format/currency';
import { formatDateTime } from '$lib/format/datetime';
import { REGISTERED } from './sections';
import { termText } from '$lib/text/terms';
import { deviceText } from '$lib/text/devices';

export const deviceColumns: Column<Device>[] = [
	{ key: 'perangkat', label: deviceText.device, align: 'left', value: (row) => row.name, sort: 'name' },
	{ key: 'stasiun', label: termText.station, align: 'left', value: (row) => (row.station_names.length > 0 ? row.station_names.join(', ') : deviceText.noStations) },
	{ key: 'dipakai', label: deviceText.lastUsed, align: 'left', value: (row) => (row.last_used_at ? formatDateTime(row.last_used_at) : EMPTY_VALUE), sort: 'last_used' },
	{ key: 'status', label: termText.status, align: 'left', value: (row) => (row.status === REGISTERED ? deviceText.registered : deviceText.waiting), sort: 'status' }
];
