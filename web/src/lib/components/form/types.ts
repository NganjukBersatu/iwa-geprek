export type FieldKind = 'text' | 'number' | 'select' | 'toggle' | 'date';

export type FieldOption = { value: string; label: string };

export type Field = {
	key: string;
	label: string;
	kind?: FieldKind;
	options?: FieldOption[];
	required?: boolean;
	placeholder?: string;
	yes?: string;
	no?: string;
};
