"""Environment configuration read by v2, independent of the legacy config module."""
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SERVICE_ROOT = Path(__file__).resolve().parents[2]
POSTGRES_SCHEMES = ("postgresql://", "postgres://")
PSYCOPG_SCHEME = "postgresql+psycopg://"
MIN_JWT_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=SERVICE_ROOT / ".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    # Absolute life of a sign-in: 12 hours, the most the rules allow without a decision of the owner.
    jwt_expire_minutes: int = 720
    # A browser sign-in with no request for this long is refused; a tablet keeps its sign-in for the whole shift.
    session_idle_minutes: int = 30
    # Alamat publik layanan v2 ini (misalnya https://api.contoh.com); semua alamat foto dan media dibentuk dari sini.
    public_url: str = ""
    # Web origins allowed to call v2 from a browser, as a JSON list; empty means only the app (no browser) calls it.
    cors_origins: list[str] = []
    # The interactive API documentation (/docs, /redoc, /openapi.json) is off unless this is set; it shows every route to anyone who asks.
    enable_api_docs: bool = False
    # Empty means no cache: every read goes to the database, nothing else changes.
    redis_url: str = ""
    # Set by Railway on every deploy; results kept by an older deploy, whose shapes may differ, are then never read.
    railway_deployment_id: str = ""
    # Lowest Android app version, as "major.minor.patch"; empty means it is not checked. The app reads it from /v2/client-version; a call from a lower version is refused with 426, except a cashier whose cash session is still open.
    min_version_apk: str = ""
    # Lowest PWA version, as "major.minor.patch"; empty means the PWA is not checked. The web admin is never checked.
    min_version_pwa: str = ""
    # Where an outdated app is offered the current version, as a button the person taps; empty means no button is offered.
    download_url: str = ""
    # Tombol "Coba mode demo" di layar masuk web admin; isi demonya dari backend/demo/snapshot.json.gz. Isi false untuk menyembunyikannya.
    demo_enabled: bool = True
    # Hanya diisi scripts/demo_snapshot.py untuk proses seed-nya sendiri: semua koneksi proses itu menulis ke skema ini, bukan ke data asli.
    seed_schema: str = Field("", pattern=r"^([a-z][a-z0-9_]{0,30})?$")

    # The web server that runs beside this one in the same container; every page request is handed to it.
    web_upstream: str = "http://127.0.0.1:3000"

    bucket_name: str = Field("", validation_alias=AliasChoices("BUCKET_NAMA", "BUCKET"))
    bucket_endpoint: str = Field("", validation_alias=AliasChoices("BUCKET_ENDPOINT", "ENDPOINT"))
    bucket_access_key_id: str = Field("", validation_alias=AliasChoices("BUCKET_ACCESS_KEY_ID", "ACCESS_KEY_ID"))
    bucket_secret_access_key: str = Field(
        "", validation_alias=AliasChoices("BUCKET_SECRET_ACCESS_KEY", "SECRET_ACCESS_KEY")
    )
    bucket_region: str = Field("auto", validation_alias=AliasChoices("BUCKET_REGION", "REGION"))
    bucket_address_style: str = Field("auto", validation_alias=AliasChoices("BUCKET_GAYA_ALAMAT"))

    @field_validator("bucket_name", "bucket_endpoint", "bucket_access_key_id", "bucket_secret_access_key", "bucket_region", "bucket_address_style")
    @classmethod
    def _without_stray_spaces(cls, value: str) -> str:
        """A space pasted around a bucket value is invisible in the dashboard yet makes every upload fail."""
        return value.strip()

    @field_validator("jwt_secret_key")
    @classmethod
    def _long_enough_secret(cls, secret: str) -> str:
        """Tokens are signed with this; a short or guessable value lets anyone mint a token for any account."""
        if len(secret) < MIN_JWT_SECRET_LENGTH:
            raise ValueError(f"JWT_SECRET_KEY must be at least {MIN_JWT_SECRET_LENGTH} characters; generate one with: python -c \"import secrets; print(secrets.token_urlsafe(48))\"")
        return secret

    @field_validator("database_url")
    @classmethod
    def _use_installed_driver(cls, url: str) -> str:
        """Railway hands out postgresql://, which SQLAlchemy reads as the psycopg2 driver that is not installed."""
        for scheme in POSTGRES_SCHEMES:
            if url.startswith(scheme):
                return PSYCOPG_SCHEME + url[len(scheme):]
        return url

    @field_validator("public_url")
    @classmethod
    def _plain_public_url(cls, url: str) -> str:
        cleaned = url.strip().rstrip("/")
        if cleaned and not cleaned.lower().startswith(("http://", "https://")):
            raise ValueError("PUBLIC_URL harus diawali http:// atau https://")
        return cleaned

    @property
    def bucket_active(self) -> bool:
        return all((self.bucket_name, self.bucket_endpoint, self.bucket_access_key_id, self.bucket_secret_access_key))


settings = Settings()
