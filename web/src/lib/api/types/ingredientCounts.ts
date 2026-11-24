import type { Schemas } from '../contract';

export type IngredientCount = Schemas['CountOut'];
export type IngredientCountDetail = Schemas['CountDetailOut'];
export type IngredientCountRunning = Schemas['RunningCountOut'];
export type IngredientCountOpenSessions = Schemas['OpenSessionsOut'];
export type IngredientCountDraft = Schemas['CountDraftOut'];
export type IngredientCountDraftLines = Schemas['CountDraftIn'];
export type IngredientCountChange = Schemas['CountChangeOut'];
export type IngredientCountChanges = Schemas['CountChangePageOut'];
export type IngredientCountLines = Schemas['CountLinesIn'];
/** Only the bulk route takes this body, so the contract does not describe it. */
export type IngredientOpening = { ingredient_id: string; opening: string; from_date: string };
export type IngredientCountClose = Schemas['CountCloseIn'];
export type IngredientClosingPeriod = Schemas['ClosingPeriodOut'];
export type IngredientOpeningStatus = Schemas['OpeningStatusOut'];
