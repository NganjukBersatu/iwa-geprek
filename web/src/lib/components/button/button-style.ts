/** Focus ring of every button: 2 px, 2 px outside the edge in near-black, so the white gap and the ring read on any surface (6.6.10). */
const focusRing = 'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-ink';

/** The colour change of hover and pressed takes 70 ms, and none when the person asked for less motion. */
const stateMotion = 'transition-colors duration-(--duration-instant) motion-reduce:transition-none';

/** Size of every header and toolbar button: 32 px with a mouse, and the 44 px touch target everywhere else. */
export const controlSize = `px-2.5 text-control pointer-fine:h-8 pointer-fine:min-h-0! pointer-fine:min-w-0! ${focusRing} ${stateMotion}`;

/** The small size for a button inside a table row: 28 px with a mouse. */
export const smallSize = `px-2.5 text-xs pointer-fine:h-7 pointer-fine:min-h-0! pointer-fine:min-w-0! ${focusRing} ${stateMotion}`;

/** The main action: filled brand, darker on hover, darker again while pressed. */
export const primaryStyle = 'bg-brand text-brand-on not-disabled:hover:bg-brand-hover not-disabled:active:bg-brand-pressed';

/** The tertiary button, for a less important action that may stand alone: brand outline on white, tinted on hover and when pressed. */
export const tertiaryStyle = 'border border-brand bg-white text-brand not-disabled:hover:bg-brand-soft not-disabled:active:bg-brand-page';

/** A light red fill for a destructive row action: it reads as a button on white rows and on the tinted hover row. */
export const dangerSoftStyle = 'border border-danger-200 bg-danger-50 text-danger-700 not-disabled:hover:border-danger-500 not-disabled:active:bg-danger-200';

/** The light fills of the other statuses, shaped like the light red one: a green, blue or yellow choice among equals, such as the attendance statuses. */
export const successSoftStyle = 'border border-success-200 bg-success-50 text-success-700 not-disabled:hover:border-success-500 not-disabled:active:bg-success-200';
export const infoSoftStyle = 'border border-info-200 bg-info-50 text-info-700 not-disabled:hover:border-info-500 not-disabled:active:bg-info-200';
export const warningSoftStyle = 'border border-warning-200 bg-warning-50 text-warning-700 not-disabled:hover:border-warning-500 not-disabled:active:bg-warning-200';

/** A destructive action: filled red, darker on hover, darker again while pressed. */
export const dangerStyle = 'bg-danger-700 text-white not-disabled:hover:bg-danger-hover not-disabled:active:bg-danger-pressed';

/** The cancel button of a dialog: red outline on white, tinted on hover and when pressed. */
export const dangerOutlineStyle = 'border border-danger-500 bg-white text-danger-700 not-disabled:hover:bg-danger-50 not-disabled:active:bg-danger-200';

/** A button that is switched on, such as an open filter: a 2 px dark green line, a bolder label, and a check mark added by Button, so colour is never the only sign (6.4.12, 6.6.9). */
export const selectedStyle = 'border-2 border-brand-ink bg-brand-ink-soft font-bold text-brand-ink not-disabled:active:bg-brand-ink-line';

/** The secondary button, the opposite action of a main one (Batal): dark outline on white. The menu and filter buttons share it. */
export const secondaryStyle = 'border border-brand-ink bg-white text-brand-ink not-disabled:hover:bg-brand-soft not-disabled:active:bg-brand-page';
