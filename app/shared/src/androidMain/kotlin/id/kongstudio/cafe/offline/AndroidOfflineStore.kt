package id.kongstudio.cafe.offline

import android.content.Context
import app.cash.sqldelight.driver.android.AndroidSqliteDriver
import id.kongstudio.cafe.offline.db.OfflineDatabase

private const val DatabaseName = "offline.db"

/** Satu penyimpanan lokal per aplikasi; berkas basis datanya hidup di folder privat aplikasi. */
fun createOfflineStore(context: Context): OfflineStore =
    OfflineStore(AndroidSqliteDriver(OfflineDatabase.Schema, context.applicationContext, DatabaseName))
