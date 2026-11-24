import type { Schemas } from '../contract';

export type DepositDays = Schemas['DepositDaysOut'];
export type DepositDay = Schemas['DepositDayStateOut'];
export type DepositSummary = Schemas['DepositSummaryOut'];
export type Deposit = Schemas['DepositOut'];
export type DepositCreate = Schemas['DepositIn'];
export type DepositStatus = DepositDay['status'];
export type DayKey = Schemas['DayKey'];
export type DayState = Schemas['DayStateOut'];
export type DayStatesAsk = Schemas['DayStatesIn'];
