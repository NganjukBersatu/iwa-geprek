export type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'tertiary' | 'dangerSoft' | 'dangerOutline' | 'successSoft' | 'infoSoft' | 'warningSoft';

export type Action = {
	label: string;
	icon: string;
	onclick: () => void;
	disabled?: boolean;
	hint?: string;
	description?: string;
	danger?: boolean;
	active?: boolean;
	items?: Action[];
};
