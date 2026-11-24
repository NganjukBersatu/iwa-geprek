import { browser } from '$app/environment';
import { api } from '$lib/api';
import type { Ability, Screen, ScreenAccess } from '$lib/api/types';
import { live } from '$lib/live/live';
import { PAGES, type Page } from '$lib/nav/pages';
import { getUser, USER_CHANGED_EVENT } from './session';

type Known = { kind: 'known'; owner: string; screens: ReadonlySet<Screen>; abilities: ReadonlySet<Ability> };
type State = { kind: 'loading'; owner: string } | { kind: 'failed'; owner: string } | Known;
/** pending: the answer for this account is still on its way, so nothing is shown or decided yet. */
export type ScreenAccessState = 'open' | 'closed' | 'pending';

const STORE_PREFIX = 'web.access.';
// A changed role or a person moved to another role changes what opens.
const ACCESS_TABLES = ['roles', 'users'];

/** What the signed-in account may open and use, as the server works it out from the same gates that guard its routes; no screen spells out a permission key. */
class Access {
	#state = $state<State>({ kind: 'loading', owner: '' });
	#asked = '';
	#ticket = 0;
	#listening = false;

	/** Whether a menu entry or a link to this screen is shown. */
	opens(screen: Screen): boolean {
		return this.screen(screen) === 'open';
	}

	/** Whether a part inside a screen is shown and loaded; unknown counts as no, since the server would refuse it anyway. */
	allows(ability: Ability): boolean {
		const state = this.#current();
		return state.kind === 'known' && state.abilities.has(ability);
	}

	/** A failed first fetch leaves the screen to the server, which still refuses its data. */
	screen(screen: Screen): ScreenAccessState {
		const state = this.#current();
		if (state.kind === 'loading') return 'pending';
		if (state.kind === 'failed') return 'open';
		return state.screens.has(screen) ? 'open' : 'closed';
	}

	/** The first screen in sidebar order the account may open, where a closed address sends it. */
	firstOpen(): Page | undefined {
		return Object.values(PAGES).find((page) => this.opens(page.screen));
	}

	/** Asks again after a failed fetch; called on navigation, so a retry never loops on its own. */
	retry(): void {
		const owner = getUser()?.id ?? '';
		if (owner && this.#state.kind === 'failed' && this.#state.owner === owner) void this.#load(owner);
	}

	#current(): State {
		const owner = getUser()?.id ?? '';
		if (owner && this.#asked !== owner) {
			this.#asked = owner;
			// Called while a template renders, where state may not change, so the answer is read a moment later.
			queueMicrotask(() => this.#start(owner));
		}
		return this.#state.owner === owner ? this.#state : { kind: 'loading', owner };
	}

	#start(owner: string): void {
		const saved = read(owner);
		this.#state = saved ? known(owner, saved) : { kind: 'loading', owner };
		this.#listen();
		void this.#load(owner);
	}

	async #load(owner: string): Promise<void> {
		const mine = ++this.#ticket;
		try {
			const answer = await api.screens.mine();
			if (mine !== this.#ticket) return;
			this.#state = known(owner, answer);
			write(owner, answer);
		} catch {
			// An answer already known stays until the next signal.
			if (mine === this.#ticket && this.#state.kind !== 'known') this.#state = { kind: 'failed', owner };
		}
	}

	#listen(): void {
		if (this.#listening || !browser) return;
		this.#listening = true;
		const again = (): void => {
			const owner = getUser()?.id ?? '';
			if (owner) void this.#load(owner);
		};
		live.on(ACCESS_TABLES, again);
		window.addEventListener(USER_CHANGED_EVENT, again);
	}
}

function known(owner: string, answer: ScreenAccess): Known {
	return { kind: 'known', owner, screens: new Set(answer.screens), abilities: new Set(answer.abilities) };
}

function read(owner: string): ScreenAccess | null {
	if (!browser) return null;
	try {
		const raw = localStorage.getItem(STORE_PREFIX + owner);
		const saved = raw ? (JSON.parse(raw) as Partial<ScreenAccess>) : null;
		return saved && Array.isArray(saved.screens) && Array.isArray(saved.abilities) ? { screens: saved.screens, abilities: saved.abilities } : null;
	} catch {
		return null;
	}
}

function write(owner: string, answer: ScreenAccess): void {
	try {
		localStorage.setItem(STORE_PREFIX + owner, JSON.stringify(answer));
	} catch {}
}

export const access = new Access();
