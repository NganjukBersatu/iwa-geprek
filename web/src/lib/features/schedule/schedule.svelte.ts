import { userMessage } from '$lib/api/user-message';
import { api } from "$lib/api";
import type {
  Assignment,
  AssignmentUpdate,
  AttendanceRecord,
  DayOff,
  PoolUser,
  Role,
  ShiftCode,
} from "$lib/api/types";
import { access } from "$lib/auth/access.svelte";
import { toast } from "$lib/components/feedback/toast.svelte";
import { Filters } from "$lib/components/filter/filters.svelte";
import { ListSort, sortKeys } from "$lib/components/table/list-sort.svelte";
import {
  shiftDays,
  WEEK_PRESETS,
  DATE_PRESETS,
  type DateRange,
} from "$lib/date/range";
import { ManageState } from "../manage/manage.svelte";
import { branchList } from "$lib/stores/branch";
import { assignmentColumns } from "./columns";
import { termText } from '$lib/text/terms';
import { scheduleText } from '$lib/text/schedule';
import { format } from '$lib/text/format';

export type ScheduleQuery = { branch: string | null; range: DateRange | null };
export type ScheduleView = "board" | "grid";

const MAX_DAYS = 62;

export class ScheduleState extends ManageState<Assignment> {
  readonly filters = new Filters([
    { kind: "select", key: "cabang", label: termText.branch, options: [] },
    {
      kind: "date",
      key: "rentang",
      label: termText.range,
      presets: [...WEEK_PRESETS, ...DATE_PRESETS],
      reach: "future",
      maxDays: MAX_DAYS,
      empty: "week",
    },
  ]);

  readonly sort = new ListSort(
    "jadwal",
    sortKeys(assignmentColumns(() => undefined)),
    () => void this.queryChanged(),
  );

  private get permittedToArrange(): boolean {
    return access.allows("arrange_schedule");
  }

  get canMarkAttendance(): boolean {
    return access.allows("mark_attendance");
  }

  outlets = $state<{ id: string; name: string }[]>([]);
  view = $state<ScheduleView>("board");
  pool = $state<PoolUser[]>([]);
  codes = $state<ShiftCode[]>([]);
  roles = $state<Role[]>([]);
  daysOff = $state<DayOff[]>([]);
  attendance = $state<AttendanceRecord[]>([]);
  range = $state<DateRange | null>(null);
  working = $state(false);
  /** True when attendance could not be read, so the board shows no marks and the attendance buttons wait for a reload. */
  attendanceFailed = $state(false);

  releasing = $state<Assignment | null>(null);
  releasingOff = $state<DayOff | null>(null);
  changeOpen = $state(false);
  bulkRemoveOpen = $state(false);

  get canArrange(): boolean {
    return this.permittedToArrange;
  }

  get query(): ScheduleQuery {
    return {
      branch: this.filters.get("cabang"),
      range: this.filters.range("rentang"),
    };
  }

  readonly dates = $derived.by((): string[] => {
    const range = this.range;
    if (!range) return [];
    const days: string[] = [];
    for (
      let day = range.from;
      day <= range.to && days.length < MAX_DAYS;
      day = shiftDays(day, 1)
    )
      days.push(day);
    return days;
  });

  readonly codeById = $derived(
    new Map(this.codes.map((code) => [code.id, code])),
  );
  readonly workCodes = $derived(this.codes.filter((code) => !code.is_day_off));
  readonly dayOffCodes = $derived(this.codes.filter((code) => code.is_day_off));
  /** Only the codes that appear in the range on screen, so the legend stays short. */
  readonly usedCodes = $derived.by(() => {
    const used = new Set([
      ...this.items.map((item) => item.shift_code_id),
      ...this.daysOff.map((item) => item.shift_code_id),
    ]);
    return this.codes
      .filter((code) => used.has(code.id))
      .sort((a, b) => a.code.localeCompare(b.code));
  });
  /** The legend per branch, because the same code text can mean different hours in each branch. */
  readonly legend = $derived.by(() => {
    const groups = new Map<string, ShiftCode[]>();
    for (const code of this.usedCodes)
      groups.set(code.outlet_id, [...(groups.get(code.outlet_id) ?? []), code]);
    return [...groups]
      .map(([outletId, codes]) => ({
        outletId,
        name:
          this.outlets.find((outlet) => outlet.id === outletId)?.name ??
          termText.branch,
        codes,
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
  });
  readonly people = $derived.by(() => {
    const people = new Map<string, string>();
    for (const person of this.pool) people.set(person.id, person.username);
    for (const item of this.items)
      people.set(item.user_id, item.user_username);
    for (const item of this.daysOff)
      people.set(item.user_id, item.user_username);
    return [...people].sort((a, b) => a[1].localeCompare(b[1]));
  });

  private readonly attendanceIndex = $derived.by(() => {
    const bySchedule = new Map<string, AttendanceRecord>();
    const bySlot = new Map<string, AttendanceRecord>();
    for (const record of this.attendance) {
      if (record.schedule_id && !bySchedule.has(record.schedule_id))
        bySchedule.set(record.schedule_id, record);
      if (record.shift_code) {
        const key = `${record.user_id}|${record.date}|${record.shift_code}`;
        if (!bySlot.has(key)) bySlot.set(key, record);
      }
    }
    return { bySchedule, bySlot };
  });

  protected async fetch(): Promise<void> {
    const query = this.query;
    this.range = query.range;
    const outlets = await branchList();
    this.outlets = outlets;
    this.filters.setOptions(
      "cabang",
      outlets.map((outlet) => ({ value: outlet.id, label: outlet.name })),
    );
    const params = {
      start: query.range?.from,
      end: query.range?.to,
      outlet_id: query.branch ?? undefined,
    };
    const [assignments, daysOff, codes, roles, pool] = await Promise.all([
      api.schedule.assignments.list({ ...params, sort: this.sort.param }),
      api.schedule.daysOff.list(params),
      api.schedule.codes(),
      api.roles.list(),
      this.permittedToArrange
        ? api.schedule.pool({ outlet_id: params.outlet_id })
        : Promise.resolve<PoolUser[]>([]),
    ]);
    this.items = assignments;
    this.total = assignments.length;
    this.daysOff = daysOff;
    this.codes = codes;
    this.roles = roles;
    this.pool = pool;
    this.attendance = [];
    this.attendanceFailed = false;
    if (!this.canMarkAttendance) return;
    try {
      this.attendance = await api.attendance.range({
        start: query.range?.from,
        end: query.range?.to,
      });
    } catch {
      this.attendanceFailed = true;
    }
  }

  protected label(item: Assignment): string {
    return `${item.user_username} · ${item.date}`;
  }

  itemsOn = (date: string) => this.items.filter((item) => item.date === date);
  daysOffOn = (date: string) =>
    this.daysOff.filter((item) => item.date === date);
  codeOf = (id: string | null | undefined) =>
    id ? this.codeById.get(id) : undefined;

  attendanceFor(item: Assignment): AttendanceRecord | undefined {
    const code = this.codeOf(item.shift_code_id)?.code;
    const slot = code
      ? this.attendanceIndex.bySlot.get(`${item.user_id}|${item.date}|${code}`)
      : undefined;
    return this.attendanceIndex.bySchedule.get(item.id) ?? slot;
  }

  /** Runs one change, then reloads, because a small board is better always right than quickly stale. */
  private async act(
    work: () => Promise<unknown>,
    success: string,
    failure: string,
    reloadFirst = false,
  ): Promise<boolean> {
    this.working = true;
    try {
      await work();
      await this.load();
      toast.show(success);
      return true;
    } catch (error) {
      toast.show(userMessage(error, failure), "error");
      if (reloadFirst) await this.load();
      return false;
    } finally {
      this.working = false;
    }
  }

  async move(item: Assignment, date: string): Promise<void> {
    if (item.date === date) return;
    await this.act(
      () => api.schedule.assignments.update(item.id, { date }),
      format(scheduleText.assignmentMoved, { name: item.user_username }),
      scheduleText.moveFailed,
    );
  }

  async swap(first: Assignment, second: Assignment): Promise<void> {
    if (first.user_id === second.user_id) return;
    await this.act(
      () => api.schedule.assignments.swap(first.id, second.id),
      scheduleText.shiftSwapped,
      scheduleText.swapFailed,
    );
  }

  askRelease(item: Assignment): void {
    this.releasing = item;
  }

  async confirmRelease(): Promise<void> {
    const item = this.releasing;
    if (!item) return;
    this.releasing = null;
    await this.act(
      () => api.schedule.assignments.remove(item.id),
      format(scheduleText.unassigned, { name: item.user_username }),
      scheduleText.unassignFailed,
    );
  }

  async confirmReleaseOff(): Promise<void> {
    const item = this.releasingOff;
    if (!item) return;
    this.releasingOff = null;
    await this.act(
      () => api.schedule.daysOff.remove(item.id),
      format(scheduleText.dayOffUnassigned, { name: item.user_username }),
      scheduleText.unassignDayOffFailed,
    );
  }

  closeDialogs(): void {
    this.releasing = null;
    this.releasingOff = null;
    this.changeOpen = false;
    this.bulkRemoveOpen = false;
    this.actionError = "";
  }

  async changeSelected(
    changes: Record<string, string | number | boolean>,
  ): Promise<void> {
    await this.bulk(
      "diubah",
      (ids) =>
        api.schedule.assignments.bulk.update(ids, changes as AssignmentUpdate),
      () => (this.changeOpen = false),
    );
  }

  async removeSelected(): Promise<void> {
    await this.bulk(
      "dihapus",
      (ids) => api.schedule.assignments.bulk.remove(ids),
      () => (this.bulkRemoveOpen = false),
    );
  }
}
