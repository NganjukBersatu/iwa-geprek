import type { MenuCategoryRecord } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE, formatNumber } from '$lib/format/currency';
import { termText } from '$lib/text/terms';

export const menuCategoryColumns: Column<MenuCategoryRecord>[] = [
	{ key: 'kategori', label: termText.category, align: 'left', value: (row) => row.name, sort: 'name' },
	{ key: 'stasiun', label: termText.station, align: 'left', value: (row) => row.station_name ?? termText.notSet, sort: 'station' },
	{ key: 'menu', label: termText.menu, value: (row) => (row.menu_count > 0 ? formatNumber(row.menu_count, 0) : EMPTY_VALUE), sort: 'menus' }
];
