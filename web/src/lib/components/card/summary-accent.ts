export type SummaryAccent = 'primary' | 'accent' | 'ink' | 'plain' | 'soft' | 'green' | 'red';

/** One colour pair per summary card: the card surface, and the solid fill that its icon and change badge share. */
export const summaryAccents: Record<SummaryAccent, { surface: string; solid: string }> = {
	primary: { surface: 'border-brand-tint bg-brand-page', solid: 'bg-brand text-brand-on' },
	accent: { surface: 'border-brand-accent-line bg-brand-accent-soft', solid: 'bg-brand-accent text-brand-ink' },
	ink: { surface: 'border-brand-ink-line bg-brand-ink-soft', solid: 'bg-brand-ink text-brand-on' },
	green: { surface: 'border-success-200 bg-success-50', solid: 'bg-success-700 text-brand-on' },
	red: { surface: 'border-danger-200 bg-danger-50', solid: 'bg-danger-700 text-brand-on' },
	plain: { surface: 'border-brand-line bg-white', solid: 'bg-brand-page text-brand' },
	soft: { surface: 'border-brand-tint bg-brand-soft', solid: 'bg-brand-tint text-brand-ink' }
};
