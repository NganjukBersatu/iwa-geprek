import type { Schemas } from '../contract';

export type LeaveRequest = Schemas['LeaveRequestOut'];
export type LeaveRequestPage = Schemas['LeaveRequestPageOut'];
export type LeaveDecision = Schemas['DecisionIn'];
export type LeaveStatus = LeaveRequest['status'];
