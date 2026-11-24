import type { Schemas } from '../contract';

export type Expense = Schemas['ExpenseOut'];
export type ExpensePage = Schemas['ExpensePageOut'];
export type ExpenseCreate = Schemas['ExpenseCreateIn'];
export type ExpenseUpdate = Schemas['ExpenseUpdateIn'];
export type SessionChoice = Schemas['SessionChoiceOut'];
export type SessionChoicePage = Schemas['SessionChoicePageOut'];
/** ExpenseReceiptIn travels as a JSON form field next to the photo, so the schema does not list it; built from the create shape. */
export type ExpenseReceipt = Pick<ExpenseCreate, 'fund_source' | 'note' | 'buyer' | 'session_id'> & {
	items: Pick<ExpenseCreate, 'item_name' | 'amount' | 'ingredient_id' | 'quantity'>[];
};
export type ReceiptReading = Schemas['ReceiptReadingOut'];
export type ReceiptLine = Schemas['ReceiptLineOut'];
export type IngredientChoice = Schemas['IngredientChoiceOut'];
export type BuyerChoice = Schemas['BuyerChoiceOut'];
