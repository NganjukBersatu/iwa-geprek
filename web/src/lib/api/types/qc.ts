import type { Schemas } from '../contract';

export type NonCashChecks = Schemas['NonCashChecksOut'];
export type NonCashCheckRow = Schemas['NonCashCheckRowOut'];
export type CheckStatus = NonCashCheckRow['status'];
