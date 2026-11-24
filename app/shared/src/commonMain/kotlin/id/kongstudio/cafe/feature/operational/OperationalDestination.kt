package id.kongstudio.cafe.feature.operational

import id.kongstudio.cafe.feature.access.Permission
import androidx.compose.ui.graphics.vector.ImageVector
import id.kongstudio.cafe.feature.access.UserAccess
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.group_cashier
import id.kongstudio.cafe.resources.group_customers
import id.kongstudio.cafe.resources.group_device
import id.kongstudio.cafe.resources.group_finance
import id.kongstudio.cafe.resources.group_inventory
import id.kongstudio.cafe.resources.group_products
import id.kongstudio.cafe.resources.group_session
import id.kongstudio.cafe.resources.nav_cashier
import id.kongstudio.cafe.resources.nav_promotions
import id.kongstudio.cafe.resources.nav_recipes
import id.kongstudio.cafe.resources.nav_variants_extras
import id.kongstudio.cafe.resources.nav_menu_manage
import id.kongstudio.cafe.resources.nav_my_session
import id.kongstudio.cafe.resources.nav_visitor_categories
import id.kongstudio.cafe.resources.nav_expenses
import id.kongstudio.cafe.resources.nav_extra_funds
import id.kongstudio.cafe.resources.nav_info
import id.kongstudio.cafe.resources.nav_ingredient_counts
import id.kongstudio.cafe.resources.nav_ingredient_list
import id.kongstudio.cafe.resources.nav_ingredient_receipts
import id.kongstudio.cafe.resources.nav_ingredient_waste
import id.kongstudio.cafe.resources.nav_offline
import id.kongstudio.cafe.resources.nav_order_notes
import id.kongstudio.cafe.resources.nav_printer
import id.kongstudio.cafe.resources.nav_resale_stock
import id.kongstudio.cafe.feature.printer.TabletMode
import id.kongstudio.cafe.resources.nav_open_bill_setting
import id.kongstudio.cafe.resources.nav_open_bills
import id.kongstudio.cafe.resources.nav_order_history
import id.kongstudio.cafe.resources.nav_stations
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.StringResource

internal enum class OperationalGroup(val label: StringResource, val icon: ImageVector) {
    Cashier(Res.string.group_cashier, AppIcons.Cart),
    Session(Res.string.group_session, AppIcons.Clock),
    Products(Res.string.group_products, AppIcons.Tag),
    Inventory(Res.string.group_inventory, AppIcons.Category),
    Customers(Res.string.group_customers, AppIcons.UsersGroup),
    Finance(Res.string.group_finance, AppIcons.Cash),
    Device(Res.string.group_device, AppIcons.Printer),
}

/** Satu tujuan di tablet operasional: [permissions] mengikuti izin peran (salah satu cukup, kosong selalu tampil), dan [shownWhileUnknown] menjaga kasir terbuka selama izin belum terbaca. */
internal enum class OperationalDestination(
    val label: StringResource,
    val icon: ImageVector,
    val group: OperationalGroup,
    val permissions: List<Permission> = emptyList(),
    val shownWhileUnknown: Boolean = false,
) {
    Cashier(Res.string.nav_cashier, AppIcons.Cart, OperationalGroup.Cashier, listOf(Permission.OrderCreate), true),
    Stations(Res.string.nav_stations, AppIcons.Dashboard, OperationalGroup.Cashier, listOf(Permission.OrderCreate, Permission.OrderStatus)),
    // Pengganti Papan Stasiun di tablet Mode Kasir: daftar pesanan sesi, cetak ulang, dan pengajuan pembatalan.
    OrderHistory(Res.string.nav_order_history, AppIcons.History, OperationalGroup.Cashier, listOf(Permission.OrderCreate)),
    OpenBills(Res.string.nav_open_bills, AppIcons.Receipt, OperationalGroup.Cashier, listOf(Permission.OrderCreate)),
    MySession(Res.string.nav_my_session, AppIcons.Clock, OperationalGroup.Session, listOf(Permission.SessionOpen)),
    ExtraFunds(Res.string.nav_extra_funds, AppIcons.CashBanknote, OperationalGroup.Cashier, listOf(Permission.OverpaymentView)),
    MenuManage(
        Res.string.nav_menu_manage,
        AppIcons.Coffee,
        OperationalGroup.Products,
        listOf(Permission.MenuManage, Permission.MenuAvailability),
    ),
    AddOns(
        Res.string.nav_variants_extras,
        AppIcons.Adjustments,
        OperationalGroup.Products,
        listOf(Permission.VariantManage, Permission.ExtraManage),
    ),
    Recipes(Res.string.nav_recipes, AppIcons.KitchenTools, OperationalGroup.Products, listOf(Permission.RecipeDetail, Permission.RecipeManage)),
    Promotions(Res.string.nav_promotions, AppIcons.Discount, OperationalGroup.Products, listOf(Permission.PromoManage)),
    OrderNotes(Res.string.nav_order_notes, AppIcons.Notes, OperationalGroup.Products, listOf(Permission.ReferenceManage)),
    VisitorCategories(
        Res.string.nav_visitor_categories,
        AppIcons.Category,
        OperationalGroup.Customers,
        listOf(Permission.VisitorManage),
    ),
    IngredientList(
        Res.string.nav_ingredient_list,
        AppIcons.Category,
        OperationalGroup.Inventory,
        listOf(Permission.StockView, Permission.StockReceive, Permission.StockAdjust, Permission.StockCount, Permission.StockClosePeriod),
    ),
    IngredientReceipts(Res.string.nav_ingredient_receipts, AppIcons.Cart, OperationalGroup.Inventory, listOf(Permission.StockReceive)),
    IngredientWaste(Res.string.nav_ingredient_waste, AppIcons.Adjustments, OperationalGroup.Inventory, listOf(Permission.StockAdjust)),
    IngredientCounts(Res.string.nav_ingredient_counts, AppIcons.Wallet, OperationalGroup.Inventory, listOf(Permission.StockCount, Permission.StockClosePeriod)),
    ResaleStock(
        Res.string.nav_resale_stock,
        AppIcons.Tag,
        OperationalGroup.Inventory,
        listOf(Permission.StockView, Permission.StockReceive, Permission.StockAdjust, Permission.StockCount),
    ),
    Printer(Res.string.nav_printer, AppIcons.Printer, OperationalGroup.Device),
    OpenBillSetting(Res.string.nav_open_bill_setting, AppIcons.Receipt, OperationalGroup.Device, listOf(Permission.OrderCreate)),
    Offline(Res.string.nav_offline, AppIcons.WifiOff, OperationalGroup.Device),
    Info(Res.string.nav_info, AppIcons.Info, OperationalGroup.Device),
    Expenses(Res.string.nav_expenses, AppIcons.Wallet, OperationalGroup.Finance, listOf(Permission.ExpenseRecord)),
    ;

    fun visibleTo(access: UserAccess?): Boolean = when {
        permissions.isEmpty() -> true
        access == null -> shownWhileUnknown
        else -> access.allows(*permissions.toTypedArray())
    }

    /** Papan Stasiun hanya di Mode Stasiun, Riwayat Pesanan hanya di Mode Kasir; keduanya disembunyikan selama mode belum terbaca. Bill Terbuka juga hanya tampil selama Open Bill menyala atau masih ada bill. */
    fun fits(mode: TabletMode?, openBillVisible: Boolean): Boolean = when (this) {
        Stations -> mode == TabletMode.Station
        OrderHistory, OpenBillSetting -> mode == TabletMode.Cashier
        OpenBills -> mode == TabletMode.Cashier && openBillVisible
        else -> true
    }
}
