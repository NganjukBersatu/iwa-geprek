import { api } from '$lib/api';
import type { Column } from '$lib/components/table/types';
import { saveBlob } from '$lib/export/download';

export type ExportFormat = 'pdf' | 'xlsx' | 'csv';

export const EXPORT_FORMATS: { format: ExportFormat; label: string; icon: string }[] = [
	{ format: 'pdf', label: 'PDF', icon: 'file-type-pdf' },
	{ format: 'xlsx', label: 'Excel', icon: 'file-type-xls' },
	{ format: 'csv', label: 'CSV', icon: 'file-type-csv' }
];

/** What a screen lends to the download menu: its title, the columns it shows, and a way to get the rows to put in. */
export type Exporter<T> = { title: string; columns: Column<T>[]; rows: () => Promise<T[]> };

/** The one way to download a list: the rows go through the same columns the table shows, and the server builds the file. Returns how many rows went in. */
export async function exportTable<T>(format: ExportFormat, exporter: Exporter<T>): Promise<number> {
	const rows = await exporter.rows();
	if (rows.length === 0) return 0;
	const { blob, filename } = await api.exports.table({
		format,
		title: exporter.title,
		columns: exporter.columns.map((column) => ({ label: column.label, align: column.align === 'left' ? 'left' : 'right' })),
		rows: rows.map((row) => exporter.columns.map((column) => column.value(row)))
	});
	saveBlob(blob, filename ?? `${exporter.title}.${format}`);
	return rows.length;
}
