/** Nama token warna tema app; kelas ditulis utuh supaya Tailwind menemukannya. */
export type ColorToken =
	| 'background'
	| 'surface'
	| 'surface-accent'
	| 'accent'
	| 'outline'
	| 'primary'
	| 'on-primary'
	| 'on-primary-muted'
	| 'on-primary-subtle'
	| 'content'
	| 'content-muted'
	| 'divider'
	| 'scrim'
	| 'selected'
	| 'danger'
	| 'danger-container'
	| 'on-danger-container'
	| 'warning'
	| 'warning-container'
	| 'info'
	| 'success'
	| 'violet'
	| 'rose'
	| 'dim';

export const textColor: Record<ColorToken, string> = {
	'background': 'text-background',
	'surface': 'text-surface',
	'surface-accent': 'text-surface-accent',
	'accent': 'text-accent',
	'outline': 'text-outline',
	'primary': 'text-primary',
	'on-primary': 'text-on-primary',
	'on-primary-muted': 'text-on-primary-muted',
	'on-primary-subtle': 'text-on-primary-subtle',
	'content': 'text-content',
	'content-muted': 'text-content-muted',
	'divider': 'text-divider',
	'scrim': 'text-scrim',
	'selected': 'text-selected',
	'danger': 'text-danger',
	'danger-container': 'text-danger-container',
	'on-danger-container': 'text-on-danger-container',
	'warning': 'text-warning',
	'warning-container': 'text-warning-container',
	'info': 'text-info',
	'success': 'text-success',
	'violet': 'text-violet',
	'rose': 'text-rose',
	'dim': 'text-dim',
};

export const bgColor: Record<ColorToken, string> = {
	'background': 'bg-background',
	'surface': 'bg-surface',
	'surface-accent': 'bg-surface-accent',
	'accent': 'bg-accent',
	'outline': 'bg-outline',
	'primary': 'bg-primary',
	'on-primary': 'bg-on-primary',
	'on-primary-muted': 'bg-on-primary-muted',
	'on-primary-subtle': 'bg-on-primary-subtle',
	'content': 'bg-content',
	'content-muted': 'bg-content-muted',
	'divider': 'bg-divider',
	'scrim': 'bg-scrim',
	'selected': 'bg-selected',
	'danger': 'bg-danger',
	'danger-container': 'bg-danger-container',
	'on-danger-container': 'bg-on-danger-container',
	'warning': 'bg-warning',
	'warning-container': 'bg-warning-container',
	'info': 'bg-info',
	'success': 'bg-success',
	'violet': 'bg-violet',
	'rose': 'bg-rose',
	'dim': 'bg-dim',
};

export const borderColor: Record<ColorToken, string> = {
	'background': 'border-background',
	'surface': 'border-surface',
	'surface-accent': 'border-surface-accent',
	'accent': 'border-accent',
	'outline': 'border-outline',
	'primary': 'border-primary',
	'on-primary': 'border-on-primary',
	'on-primary-muted': 'border-on-primary-muted',
	'on-primary-subtle': 'border-on-primary-subtle',
	'content': 'border-content',
	'content-muted': 'border-content-muted',
	'divider': 'border-divider',
	'scrim': 'border-scrim',
	'selected': 'border-selected',
	'danger': 'border-danger',
	'danger-container': 'border-danger-container',
	'on-danger-container': 'border-on-danger-container',
	'warning': 'border-warning',
	'warning-container': 'border-warning-container',
	'info': 'border-info',
	'success': 'border-success',
	'violet': 'border-violet',
	'rose': 'border-rose',
	'dim': 'border-dim',
};
