import type { Tone } from '$lib/components/card/tone';

const ROLE_TONES: Tone[] = ['info', 'success', 'category', 'warning', 'accent', 'brand'];

/** One tone per role, always the same for the same role name, so people of one role read as a group on the board. */
export function roleTone(roleName: string): Tone {
	let hash = 0;
	for (const char of roleName) hash = (hash * 31 + char.charCodeAt(0)) % ROLE_TONES.length;
	return ROLE_TONES[hash] ?? 'neutral';
}
