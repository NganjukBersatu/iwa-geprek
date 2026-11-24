import { downloadText } from '$lib/text/download';

/** `dim` darkens the background, `bloom` lets its colour open up. */
export type WelcomeMood = 'dim' | 'bloom';

export type WelcomeScene = {
	text: string;
	sub: string | null;
	mood: WelcomeMood;
	/** A silent pause before the line appears. */
	silence: number;
	hold: number;
	big: boolean;
	logo: boolean;
	spinner: boolean;
};

const scene = (text: string, hold: number, extra: Partial<Omit<WelcomeScene, 'text' | 'hold'>> = {}): WelcomeScene => ({
	text,
	hold,
	sub: null,
	mood: 'dim',
	silence: 0,
	big: false,
	logo: false,
	spinner: false,
	...extra
});

/** The thanks to the employees who carried the first version; approved by Safjar word for word, with the name of the product replaced. */
export const WELCOME_SCENES: WelcomeScene[] = [
	scene(downloadText.welcome.remember, 2600, { silence: 600 }),
	scene(downloadText.welcome.hardships, 3000),
	scene(downloadText.welcome.thanks, 3400, { silence: 1300, big: true }),
	scene(downloadText.welcome.credit, 2600),
	scene(downloadText.welcome.without, 2900),
	scene(downloadText.welcome.welcomeTo, 1900, { silence: 400 }),
	scene(downloadText.welcome.newVersion, 4200, { sub: downloadText.welcome.born, mood: 'bloom', big: true, logo: true, spinner: true })
];

/** How long a line takes to leave before the next one. */
export const WELCOME_FADE_MILLISECONDS = 650;

/** Set once the last scene has played on this device; the welcome cannot be skipped before that. */
export const WELCOME_SEEN_KEY = 'welcome-seen';
