import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    // Plugin kotlin-android TIDAK diterapkan: AGP 9 sudah membawa dukungan Kotlin.
    alias(libs.plugins.compose.multiplatform)
    alias(libs.plugins.compose.compiler)
}

// Kunci tanda tangan rilis dibaca dari keystore.properties di luar git; tanpa berkas itu build release gagal, build debug tetap jalan.
val releaseKey = Properties().apply {
    val source = rootProject.file("keystore.properties")
    if (source.exists()) source.inputStream().use { load(it) }
}

// Identitas merek dibaca dari brand.properties hasil jawaban Copier; tanpa berkas itu build gagal sejak awal.
val brand = Properties().apply { rootProject.file("brand.properties").inputStream().use { load(it) } }

// Versi APK milik klien dibaca dari version.properties, supaya copier update tidak mengembalikannya ke versi template.
val appVersion = Properties().apply { rootProject.file("version.properties").inputStream().use { load(it) } }

android {
    namespace = "id.kongstudio.cafe.android"
    compileSdk = libs.versions.compileSdk.get().toInt()

    defaultConfig {
        // Identitas aplikasi di HP; tidak boleh diubah lagi setelah rilis karena APK baru akan dianggap aplikasi lain.
        applicationId = brand.getProperty("applicationId")
        minSdk = libs.versions.minSdk.get().toInt()
        targetSdk = libs.versions.targetSdk.get().toInt()
        versionCode = appVersion.getProperty("versionCode").toInt()
        versionName = appVersion.getProperty("versionName")
    }

    buildFeatures {
        compose = true
    }

    signingConfigs {
        create("release") {
            if (!releaseKey.isEmpty) {
                storeFile = file(releaseKey.getProperty("storeFile"))
                storePassword = releaseKey.getProperty("storePassword")
                keyAlias = releaseKey.getProperty("keyAlias")
                keyPassword = releaseKey.getProperty("keyPassword")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("release")
        }
    }
}

dependencies {
    implementation(project(":shared"))
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.core.splashscreen)
}
