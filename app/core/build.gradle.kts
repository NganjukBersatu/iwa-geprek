plugins {
    alias(libs.plugins.kotlin.multiplatform)
    alias(libs.plugins.android.kotlin.multiplatform.library)
    alias(libs.plugins.compose.multiplatform)
    alias(libs.plugins.compose.compiler)
    alias(libs.plugins.kotlin.serialization)
}

abstract class GenerateApiConfig : DefaultTask() {
    @get:Input abstract val v2BaseUrl: Property<String>
    @get:OutputDirectory abstract val outputDir: DirectoryProperty

    @TaskAction
    fun generate() {
        val file = outputDir.file("id/kongstudio/cafe/core/network/ApiConfig.kt").get().asFile
        file.parentFile.mkdirs()
        file.writeText(
            """
            package id.kongstudio.cafe.core.network

            object ApiConfig {
                const val V2_BASE_URL = "${v2BaseUrl.get()}"
            }
            """.trimIndent() + "\n"
        )
    }
}

// Alamat server dibaca dari variabel lingkungan atau berkas .env di folder app, tidak ditulis di kode.
val dotEnv = providers
    .fileContents(rootProject.layout.projectDirectory.file(".env"))
    .asText
    .map { text ->
        text.lines().map { it.trim() }
            .filter { it.isNotEmpty() && !it.startsWith("#") && "=" in it }
            .associate { it.substringBefore("=").trim() to it.substringAfter("=").trim().trim('"') }
    }
    .orElse(emptyMap())

fun apiSetting(name: String): Provider<String> = providers.environmentVariable(name)
    .orElse(dotEnv.map { it[name].orEmpty() })
    .map { raw ->
        raw.trim().trimEnd('/').also {
            require(it.startsWith("https://") || it.startsWith("http://")) {
                "Pengaturan $name belum diisi. Isi di app/.env atau variabel lingkungan."
            }
        }
    }

val generateApiConfig = tasks.register<GenerateApiConfig>("generateApiConfig") {
    v2BaseUrl.set(apiSetting("V2_BASE_URL"))
    outputDir.set(layout.buildDirectory.dir("generated/apiconfig/commonMain"))
}

kotlin {
    android {
        namespace = "id.kongstudio.cafe.core"
        compileSdk = libs.versions.compileSdk.get().toInt()
        minSdk = libs.versions.minSdk.get().toInt()
        // Dibutuhkan agar sumber daya Compose (gambar) ikut dikemas di Android.
        androidResources { enable = true }
    }

    sourceSets {
        commonMain.get().kotlin.srcDir(generateApiConfig.flatMap { it.outputDir })
        commonMain.dependencies {
            api(compose.runtime)
            api(compose.foundation)
            api(compose.ui)
            api(libs.compose.components.resources)
            implementation(libs.ktor.client.core)
            implementation(libs.ktor.client.content.negotiation)
            implementation(libs.ktor.serialization.kotlinx.json)
            implementation(libs.kotlinx.serialization.json)
            implementation(libs.coil.compose)
            implementation(libs.coil.network.ktor)
        }
        androidMain.dependencies {
            implementation(libs.ktor.client.okhttp)
            implementation(libs.androidx.activity.compose)
        }
    }
}

compose.resources {
    packageOfResClass = "id.kongstudio.cafe.resources"
    // Res dipakai juga oleh modul lain (shared, customerApp), jadi harus publik.
    publicResClass = true
}
