import { controlText } from '$lib/text/controls';
import type { Issue, IssueKind, IssueLevel } from '$lib/api/types';
import type { SummaryAccent } from '$lib/components/card/summary-accent';
import type { Tone } from '$lib/components/card/tone';
import { formatNumber, formatPercentPlain, formatRupiah } from '$lib/format/currency';
import { formatDateTime, formatTime } from '$lib/format/datetime';
import { formatDayMonth } from '$lib/date/range';
import { parseDate } from '@internationalized/date';
import { todayIso } from '$lib/date/range';
import { withFilters } from '$lib/nav/link-filters';
import { menuPath, PAGES, sessionPath, type Page } from '$lib/nav/pages';
import { issueText } from '$lib/text/issues';
import { format } from '$lib/text/format';

export type IssueRow = { main: string; meta: string; figure: string };
// Halaman detail yang membuka tepat data temuan itu lewat subject_id-nya.
type Detail = { page: Page; path: (id: string) => string };
// search: halaman daftarnya bisa dicari dengan nama temuan; day: daftarnya bisa disaring ke tanggal temuan; until: hari akhir bila temuannya mencakup beberapa hari.
type KindText = { title: string; link: Page; row: (issue: Issue) => IssueRow; detail?: Detail; search?: true; day?: true; until?: (issue: Issue) => string | null };
export type IssueLink = { path: string; page: Page };

const SESSION: Detail = { page: PAGES.sessionHistory, path: sessionPath };
const MENU: Detail = { page: PAGES.menu, path: menuPath };

export const LEVELS: { level: IssueLevel; label: string; caption: string; tone: Tone; accent: SummaryAccent; icon: string }[] = [
	{ level: 'problem', label: issueText.levelProblem, caption: issueText.levelProblemHint, tone: 'danger', accent: 'red', icon: 'alert-triangle' },
	{ level: 'warning', label: issueText.levelWarning, caption: issueText.levelWarningHint, tone: 'warning', accent: 'accent', icon: 'alert-circle' },
	{ level: 'notice', label: issueText.levelNotice, caption: issueText.levelNoticeHint, tone: 'info', accent: 'ink', icon: 'info-circle' },
	{ level: 'suggestion', label: issueText.levelSuggestion, caption: issueText.levelSuggestionHint, tone: 'brand', accent: 'primary', icon: 'bulb' }
];

const RESALE = 'resale';

const day = (issue: Issue): string => (issue.day ? formatDayMonth(issue.day) : '');
// Hari terakhir dari N hari berturut-turut yang dimulai di tanggal temuan.
const lastOfDays = (issue: Issue): string | null => (issue.day && issue.count && issue.count > 1 ? parseDate(issue.day).add({ days: issue.count - 1 }).toString() : null);
const at = (issue: Issue): string => (issue.at ? formatDateTime(issue.at) : '');
const branch = (issue: Issue): string => issue.outlet_name ?? '';
const joined = (...parts: string[]): string => parts.filter(Boolean).join(' · ');
const quantity = (value: string | null, unit: string | null): string => `${formatNumber(value)} ${unit ?? ''}`.trim();
const where = (issue: Issue): string => joined(branch(issue), issue.subject_kind === RESALE ? issueText.resale : '');

const subjectInBranch = (issue: Issue, figure = ''): IssueRow => ({ main: issue.subject, meta: branch(issue), figure });
const session = (issue: Issue, figure: string, extra = ''): IssueRow => ({
	main: issue.subject,
	meta: joined(branch(issue), format(issueText.sessionClosedAt, { at: at(issue) }), extra),
	figure
});

const TEXTS: Record<IssueKind, KindText> = {
	expense_over_income: {
		title: issueText.expenseOverIncome,
		link: PAGES.financeOverview,
		day: true,
		row: (issue) => ({ main: day(issue), meta: joined(branch(issue), format(issueText.incomeAmount, { amount: formatRupiah(issue.compared) })), figure: formatRupiah(issue.amount) })
	},
	drawer_over_cash: {
		title: issueText.drawerOverCash,
		link: PAGES.sessionHistory,
		detail: SESSION,
		row: (issue) => session(issue, format(issueText.drawerCash, { amount: formatRupiah(issue.amount) }), format(issueText.cashAmount, { amount: formatRupiah(issue.compared) }))
	},
	cash_difference: { title: issueText.sessionCashDifference, link: PAGES.sessionHistory, detail: SESSION, row: (issue) => session(issue, formatRupiah(issue.amount)) },
	float_difference: {
		title: issueText.drawerFloatMismatch,
		link: PAGES.sessionHistory,
		detail: SESSION,
		row: (issue) => session(issue, format(issueText.actualAmount, { amount: formatRupiah(issue.amount) }), format(issueText.plannedAmount, { amount: formatRupiah(issue.compared) }))
	},
	shopping_difference: {
		title: issueText.spendingFloatMismatch,
		link: PAGES.sessionHistory,
		detail: SESSION,
		row: (issue) => session(issue, format(issueText.actualAmount, { amount: formatRupiah(issue.amount) }), format(issueText.plannedAmount, { amount: formatRupiah(issue.compared) }))
	},
	session_left_open: { title: issueText.sessionNotClosed, link: PAGES.sessionHistory, detail: SESSION, row: (issue) => subjectInBranch(issue, format(issueText.openedAt, { at: at(issue) })) },
	deposit_held: {
		title: issueText.revenueNotDeposited,
		link: PAGES.financeOverview,
		day: true,
		until: () => todayIso(),
		row: (issue) => ({ main: branch(issue), meta: format(issueText.daysSince, { count: String(issue.count), day: day(issue) }), figure: formatRupiah(issue.amount) })
	},
	non_cash_unchecked: {
		title: issueText.qcNotChecked,
		link: PAGES.nonCashCheck,
		row: (issue) => ({ main: branch(issue), meta: format(issueText.daysSince, { count: String(issue.count), day: day(issue) }), figure: formatRupiah(issue.amount) })
	},
	non_cash_mismatch: {
		title: issueText.qcMismatch,
		link: PAGES.nonCashCheck,
		day: true,
		row: (issue) => ({ main: day(issue), meta: branch(issue), figure: format(issueText.differenceAmount, { amount: formatRupiah(issue.amount) }) })
	},
	overpayment: {
		title: issueText.overpayment,
		link: PAGES.overpayments,
		row: (issue) => ({ main: issue.subject, meta: joined(branch(issue), at(issue), issue.unit ?? ''), figure: formatRupiah(issue.amount) })
	},
	voids_many: {
		title: issueText.repeatedVoids,
		link: PAGES.voidsReport,
		day: true,
		row: (issue) => ({ main: issue.subject, meta: joined(branch(issue), day(issue)), figure: format(issueText.transactionsCount, { count: String(issue.count) }) })
	},
	cancellation_waiting: {
		title: issueText.pendingVoidRequests,
		link: PAGES.cancellations,
		row: (issue) => ({ main: branch(issue), meta: '', figure: format(issueText.requestsCount, { count: String(issue.count) }) })
	},
	order_off_board: {
		title: issueText.orderNotInStation,
		link: PAGES.stationMonitor,
		row: (issue) => ({ main: branch(issue), meta: '', figure: format(controlText.ordersCount, { count: String(issue.count) }) })
	},
	stock_out: { title: issueText.stockOut, link: PAGES.ingredients, search: true, row: (issue) => ({ main: issue.subject, meta: where(issue), figure: issueText.stockOutFigure }) },
	stock_negative: {
		title: issueText.stockNegative,
		link: PAGES.ingredients, search: true,
		row: (issue) => ({ main: issue.subject, meta: where(issue), figure: quantity(issue.amount, issue.unit) })
	},
	stock_low: {
		title: issueText.stockLow,
		link: PAGES.ingredients, search: true,
		row: (issue) => ({
			main: issue.subject,
			meta: joined(
				where(issue),
				format(issueText.minimumOf, { quantity: quantity(issue.compared, issue.unit) }),
				issue.days !== null ? format(issueText.runsOutIn, { days: String(Math.ceil(Number(issue.days))) }) : ''
			),
			figure: format(issueText.remainingOf, { quantity: quantity(issue.amount, issue.unit) })
		})
	},
	opening_missing: {
		title: issueText.openingMissing,
		link: PAGES.ingredientCounts,
		row: (issue) => ({ main: branch(issue), meta: format(issueText.periodStartsOn, { day: day(issue) }), figure: format(issueText.ingredientsCount, { count: String(issue.count) }) })
	},
	count_request_waiting: {
		title: issueText.countRequestWaiting,
		link: PAGES.ingredientCounts,
		row: (issue) => ({ main: branch(issue), meta: '', figure: format(issueText.requestsCount, { count: String(issue.count) }) })
	},
	count_over_tolerance: {
		title: issueText.countOverTolerance,
		link: PAGES.ingredientCounts, day: true,
		row: (issue) => ({ main: branch(issue), meta: format(issueText.periodUntil, { day: day(issue) }), figure: format(issueText.ingredientsCount, { count: String(issue.count) }) })
	},
	purchase_price_jump: {
		title: issueText.purchasePriceUp,
		link: PAGES.ingredientReceipts, search: true,
		row: (issue) => ({
			main: issue.subject,
			meta: joined(branch(issue), format(issueText.fromTo, { from: formatRupiah(issue.compared), to: formatRupiah(issue.amount) })),
			figure: format(issueText.increaseOf, { percent: formatPercentPlain(issue.percent) })
		})
	},
	ingredient_idle: { title: issueText.ingredientIdle, link: PAGES.ingredients, search: true, row: (issue) => subjectInBranch(issue) },
	ingredient_no_minimum: { title: issueText.ingredientNoMinimum, link: PAGES.ingredients, search: true, row: (issue) => ({ main: issue.subject, meta: where(issue), figure: '' }) },
	ingredient_unused: { title: issueText.ingredientUnused, link: PAGES.ingredients, search: true, row: (issue) => subjectInBranch(issue) },
	margin_below_target: {
		title: issueText.marginBelowTarget,
		link: PAGES.recipes,
		detail: MENU,
		row: (issue) => ({ main: issue.subject, meta: joined(branch(issue), format(issueText.targetOf, { percent: formatPercentPlain(issue.compared) })), figure: format(issueText.marginOf, { percent: formatPercentPlain(issue.percent) }) })
	},
	menu_without_recipe: { title: issueText.menuNoRecipe, link: PAGES.recipes, detail: MENU, row: (issue) => subjectInBranch(issue) },
	menu_should_be_variant: {
		title: issueText.menuShouldBeVariant,
		link: PAGES.menu,
		detail: MENU,
		row: (issue) => ({ main: issue.subject, meta: '', figure: format(controlText.menusCount, { count: String(issue.count) }) })
	},
	menu_unsold: { title: issueText.menuNotSold, link: PAGES.menu, detail: MENU, row: (issue) => subjectInBranch(issue) },
	promo_ending: { title: issueText.promoEndingSoon, link: PAGES.promotions, row: (issue) => ({ main: issue.subject, meta: '', figure: format(issueText.endsOn, { day: day(issue) }) }) },
	promo_unused: {
		title: issueText.promoNeverUsed,
		link: PAGES.promotions,
		row: (issue) => ({ main: issue.subject, meta: '', figure: format(issueText.runningSince, { day: day(issue) }) })
	},
	leave_waiting: {
		title: issueText.leaveRequestsPending,
		link: PAGES.leaveRequests,
		row: (issue) => subjectInBranch(issue, format(issueText.daysFrom, { count: String(issue.count), day: day(issue) }))
	},
	user_unscheduled: {
		title: issueText.employeeNotScheduled,
		link: PAGES.schedule, day: true,
		until: lastOfDays,
		row: (issue) => ({ main: issue.subject, meta: joined(branch(issue), format(issueText.startsOn, { day: day(issue) })), figure: format(issueText.emptyDaysCount, { count: String(issue.count) }) })
	},
	branch_without_users: {
		title: issueText.branchNoSchedule,
		link: PAGES.schedule, day: true,
		until: lastOfDays,
		row: (issue) => ({ main: branch(issue), meta: format(issueText.startsOn, { day: day(issue) }), figure: format(issueText.emptyDaysCount, { count: String(issue.count) }) })
	},
	no_clock_in: {
		title: issueText.noCheckIn,
		link: PAGES.schedule, day: true,
		row: (issue) => ({ main: issue.subject, meta: joined(branch(issue), issue.at ? format(issueText.dayAtTime, { day: day(issue), time: formatTime(issue.at) }) : day(issue)), figure: '' })
	},
	no_clock_out: { title: issueText.noCheckOut, link: PAGES.attendance, search: true, day: true, row: (issue) => subjectInBranch(issue, day(issue)) },
	auto_closed: { title: issueText.attendanceAutoClosed, link: PAGES.attendance, search: true, day: true, row: (issue) => subjectInBranch(issue, day(issue)) },
	late_repeated: {
		title: issueText.repeatedLate,
		link: PAGES.attendance, search: true,
		row: (issue) => ({ main: issue.subject, meta: joined(branch(issue), issueText.withinThirtyDays), figure: format(issueText.timesCount, { count: String(issue.count) }) })
	},
	overtime_open: { title: issueText.overtimeNotEnded, link: PAGES.attendance, search: true, day: true, row: (issue) => subjectInBranch(issue, day(issue)) },
	user_unplaced: { title: issueText.employeeNoBranch, link: PAGES.user, search: true, row: (issue) => ({ main: issue.subject, meta: '', figure: '' }) },
	task_missed: {
		title: issueText.outletTaskNotDone,
		link: PAGES.tasks, search: true, day: true,
		row: (issue) => ({ main: issue.subject, meta: joined(branch(issue), format(issueText.lastOn, { day: day(issue) })), figure: format(controlText.daysCount, { count: String(issue.count) }) })
	},
	device_idle: {
		title: issueText.deviceIdle,
		link: PAGES.devices,
		row: (issue) => subjectInBranch(issue, issue.at ? format(issueText.lastOn, { day: at(issue) }) : '')
	},
	device_code_expired: { title: issueText.pairingCodeExpired, link: PAGES.devices, row: (issue) => subjectInBranch(issue) }
};

export function textOf(kind: IssueKind): KindText {
	return TEXTS[kind];
}

// Tujuan satu baris: halaman detail datanya bila ada, selain itu halaman daftar jenisnya yang sudah tersaring ke temuan itu.
export function linkOf(kind: IssueKind, issue: Issue): IssueLink {
	const text = TEXTS[kind];
	if (text.detail && issue.subject_id) return { path: text.detail.path(issue.subject_id), page: text.detail.page };
	const page = text.link === PAGES.ingredients && issue.subject_kind === RESALE ? PAGES.stockItems : text.link;
	// Rentang selalu dikirim: tanggal temuan bila jenisnya bertanggal, selain itu kosong supaya halaman tujuan tidak memakai sisa rentang halaman lain.
	const filters = { branch: issue.outlet_id, search: text.search ? issue.subject : null, day: text.day ? (issue.day ?? '') : '', until: text.day ? (text.until?.(issue) ?? null) : null };
	return { path: withFilters(page.path, filters), page };
}
