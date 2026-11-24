export type Column<T> = {
	key: string;
	label: string;
	value: (row: T) => string;
	align?: 'left' | 'right';
	class?: (row: T) => string;
	/** The key the server orders this column by; a column without one cannot be sorted. */
	sort?: string;
};
