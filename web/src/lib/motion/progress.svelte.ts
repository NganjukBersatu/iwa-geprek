// A screen that is ready this fast shows no bar at all.
const SHOW_AFTER_MILLISECONDS = 120;
const DONE_MILLISECONDS = 400;
// A request that never settles does not keep the bar forever.
const GIVE_UP_MILLISECONDS = 10_000;

export type ProgressState = 'idle' | 'loading' | 'done';

/** The thin bar at the top while a screen is on its way: from leaving the old page until the requests the new page made on arrival have settled. */
class NavProgress {
	state = $state<ProgressState>('idle');
	private moving = false;
	private pending = 0;
	private showTimer: ReturnType<typeof setTimeout> | undefined;
	private hideTimer: ReturnType<typeof setTimeout> | undefined;
	private giveUpTimer: ReturnType<typeof setTimeout> | undefined;

	start(): void {
		this.moving = true;
		clearTimeout(this.hideTimer);
		clearTimeout(this.showTimer);
		clearTimeout(this.giveUpTimer);
		this.showTimer = setTimeout(() => (this.state = 'loading'), SHOW_AFTER_MILLISECONDS);
		this.giveUpTimer = setTimeout(() => this.finish(), GIVE_UP_MILLISECONDS);
	}

	/** The new page has mounted; its first requests are already on their way. */
	arrived(): void {
		this.moving = false;
		this.settle();
	}

	requestStarted(): void {
		this.pending += 1;
	}

	requestEnded(): void {
		this.pending = Math.max(0, this.pending - 1);
		this.settle();
	}

	private settle(): void {
		if (!this.moving && this.pending === 0) this.finish();
	}

	private finish(): void {
		this.moving = false;
		clearTimeout(this.showTimer);
		clearTimeout(this.giveUpTimer);
		if (this.state !== 'loading') return;
		this.state = 'done';
		this.hideTimer = setTimeout(() => (this.state = 'idle'), DONE_MILLISECONDS);
	}
}

export const navProgress = new NavProgress();
