export type Tone = 'brand' | 'accent' | 'success' | 'info' | 'category' | 'danger' | 'warning' | 'neutral';

export type ToneClasses = {
	tile: string;
	ink: string;
	pill: string;
	banner: string;
	border: string;
	surface: string;
	line: string;
};

/** Icons and bars are graphics and need 3:1 against their background (6.4.4); the light 500 steps of success and warning give only about 2:1, so those two use 700. */
export const tones: Record<Tone, ToneClasses> = {
	brand: {
		tile: 'bg-brand-soft text-brand',
		ink: 'text-brand',
		pill: 'border-brand-line bg-brand-soft text-brand',
		banner: 'border-brand-line bg-brand-soft text-brand',
		border: 'border-brand-line/60 hover:border-brand/40',
		surface: 'bg-brand-soft',
		line: 'text-brand'
	},
	accent: {
		tile: 'bg-brand-accent-soft text-brand-ink',
		ink: 'text-brand-ink',
		pill: 'border-brand-accent-line bg-brand-accent-soft text-brand-ink',
		banner: 'border-brand-accent-line bg-brand-accent-soft text-brand-ink',
		border: 'border-brand-accent-line hover:border-brand-accent',
		surface: 'bg-brand-accent-soft',
		line: 'text-brand-accent-deep'
	},
	success: {
		tile: 'bg-success-50 text-success-700',
		ink: 'text-success-700',
		pill: 'border-success-200 bg-success-50 text-success-700',
		banner: 'border-success-200 bg-success-50 text-success-700',
		border: 'border-success-200 hover:border-success-500/50',
		surface: 'bg-success-50',
		line: 'text-success-700'
	},
	info: {
		tile: 'bg-info-50 text-info-500',
		ink: 'text-info-700',
		pill: 'border-info-200 bg-info-50 text-info-700',
		banner: 'border-info-200 bg-info-50 text-info-700',
		border: 'border-info-200 hover:border-info-500/50',
		surface: 'bg-info-50',
		line: 'text-info-500'
	},
	category: {
		tile: 'bg-category-50 text-category-500',
		ink: 'text-category-700',
		pill: 'border-category-200 bg-category-50 text-category-700',
		banner: 'border-category-200 bg-category-50 text-category-700',
		border: 'border-category-200 hover:border-category-500/50',
		surface: 'bg-category-50',
		line: 'text-category-500'
	},
	danger: {
		tile: 'bg-danger-50 text-danger-500',
		ink: 'text-danger-700',
		pill: 'border-danger-200 bg-danger-50 text-danger-700',
		banner: 'border-danger-200 bg-danger-50 text-danger-700',
		border: 'border-danger-200 hover:border-danger-500/50',
		surface: 'bg-danger-50',
		line: 'text-danger-500'
	},
	warning: {
		tile: 'bg-warning-50 text-warning-700',
		ink: 'text-warning-700',
		pill: 'border-warning-200 bg-warning-50 text-warning-700',
		banner: 'border-warning-200 bg-warning-50 text-warning-700',
		border: 'border-warning-200 hover:border-warning-500/50',
		surface: 'bg-warning-50',
		line: 'text-warning-700'
	},
	neutral: {
		tile: 'bg-slate-100 text-slate-500',
		ink: 'text-slate-600',
		pill: 'border-slate-200 bg-slate-100 text-slate-600',
		banner: 'border-slate-200 bg-slate-50 text-slate-600',
		border: 'border-slate-100 hover:border-slate-200',
		surface: 'bg-slate-50',
		line: 'text-slate-500'
	}
};
