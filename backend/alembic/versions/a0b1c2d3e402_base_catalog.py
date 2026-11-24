"""base schema: units, categories, menu, variants, extras, ingredients, recipes, promos and payment methods

Revision ID: a0b1c2d3e402
Revises: a0b1c2d3e401

The v2 chain started on top of tables owned by a legacy chain that is not in this repository, so a database built from nothing
could not be created. This revision and its three siblings create those tables, in the shape the chain expects to find them:
columns that later revisions add (roles.is_admin, expenses.bahan_id, the business_day columns, ...) are left out on purpose.

Every statement is IF NOT EXISTS, so a database that already has the tables (production, staging) is left exactly as it is.
Down is a no-op: dropping the core tables would destroy data, and a mistake after release is fixed with a forward migration.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'a0b1c2d3e402'
down_revision: Union[str, Sequence[str], None] = 'a0b1c2d3e401'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS satuan (
        id VARCHAR NOT NULL,
        nama VARCHAR(20) NOT NULL,
        CONSTRAINT pk_satuan PRIMARY KEY (id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS kategori (
        id VARCHAR NOT NULL,
        jenis VARCHAR(20) NOT NULL,
        nama VARCHAR(100) NOT NULL,
        stasiun VARCHAR(10),
        stasiun_id VARCHAR,
        CONSTRAINT pk_kategori PRIMARY KEY (id)
    )
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS unique_kategori_jenis_nama ON kategori (jenis, lower(nama))
    """,
    """
    CREATE TABLE IF NOT EXISTS katalog_bahan (
        id VARCHAR NOT NULL,
        nama VARCHAR(255) NOT NULL,
        satuan_id VARCHAR,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_katalog_bahan PRIMARY KEY (id),
        CONSTRAINT fk_katalog_bahan_satuan_id_satuan FOREIGN KEY(satuan_id) REFERENCES satuan (id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_katalog_bahan_on_satuan_id ON katalog_bahan (satuan_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS bahan (
        id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        katalog_id VARCHAR,
        nama VARCHAR(255) NOT NULL,
        kategori_id VARCHAR,
        satuan_id VARCHAR,
        foto_path VARCHAR(255),
        harga_kemasan NUMERIC(12, 2) NOT NULL,
        isi_kemasan NUMERIC(12, 3) NOT NULL,
        harga_satuan NUMERIC(14, 4) NOT NULL,
        toleransi_minus NUMERIC(5, 2) NOT NULL,
        minimum NUMERIC(12, 3) NOT NULL,
        aktif BOOLEAN NOT NULL,
        tersedia BOOLEAN NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_bahan PRIMARY KEY (id),
        CONSTRAINT fk_bahan_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE RESTRICT,
        CONSTRAINT fk_bahan_katalog_id_katalog_bahan FOREIGN KEY(katalog_id) REFERENCES katalog_bahan (id) ON DELETE SET NULL,
        CONSTRAINT fk_bahan_kategori_id_kategori FOREIGN KEY(kategori_id) REFERENCES kategori (id) ON DELETE SET NULL,
        CONSTRAINT fk_bahan_satuan_id_satuan FOREIGN KEY(satuan_id) REFERENCES satuan (id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_bahan_on_outlet_id ON bahan (outlet_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_bahan_on_katalog_id ON bahan (katalog_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_bahan_on_kategori_id ON bahan (kategori_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_bahan_on_satuan_id ON bahan (satuan_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS menu_items (
        id VARCHAR NOT NULL,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        price NUMERIC(10, 2) NOT NULL,
        kategori_id VARCHAR,
        image_path VARCHAR(500),
        is_available BOOLEAN NOT NULL,
        punya_varian_suhu BOOLEAN NOT NULL,
        outlet_ids JSON,
        tax_persen NUMERIC(5, 2),
        service_persen NUMERIC(5, 2),
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_menu_items PRIMARY KEY (id),
        CONSTRAINT fk_menu_items_kategori_id_kategori FOREIGN KEY(kategori_id) REFERENCES kategori (id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_menu_items_on_kategori_id ON menu_items (kategori_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS menu_harga_outlet (
        id VARCHAR NOT NULL,
        menu_item_id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        price NUMERIC(10, 2) NOT NULL,
        CONSTRAINT pk_menu_harga_outlet PRIMARY KEY (id),
        CONSTRAINT fk_menu_harga_outlet_menu_item_id_menu_items FOREIGN KEY(menu_item_id) REFERENCES menu_items (id) ON DELETE CASCADE,
        CONSTRAINT fk_menu_harga_outlet_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE CASCADE,
        CONSTRAINT unique_menu_harga_outlet_menu_item_id_and_outlet_id UNIQUE (menu_item_id, outlet_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_menu_harga_outlet_on_outlet_id ON menu_harga_outlet (outlet_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS varian_grup (
        id VARCHAR NOT NULL,
        nama VARCHAR(80) NOT NULL,
        wajib BOOLEAN NOT NULL,
        urutan INTEGER NOT NULL,
        aktif BOOLEAN NOT NULL,
        CONSTRAINT pk_varian_grup PRIMARY KEY (id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS varian_pilihan (
        id VARCHAR NOT NULL,
        grup_id VARCHAR NOT NULL,
        nama VARCHAR(60) NOT NULL,
        warna VARCHAR(9),
        urutan INTEGER NOT NULL,
        aktif BOOLEAN NOT NULL,
        CONSTRAINT pk_varian_pilihan PRIMARY KEY (id),
        CONSTRAINT fk_varian_pilihan_grup_id_varian_grup FOREIGN KEY(grup_id) REFERENCES varian_grup (id) ON DELETE CASCADE
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_varian_pilihan_on_grup_id ON varian_pilihan (grup_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS menu_varian_grup (
        id VARCHAR NOT NULL,
        menu_item_id VARCHAR NOT NULL,
        grup_id VARCHAR NOT NULL,
        CONSTRAINT pk_menu_varian_grup PRIMARY KEY (id),
        CONSTRAINT fk_menu_varian_grup_menu_item_id_menu_items FOREIGN KEY(menu_item_id) REFERENCES menu_items (id) ON DELETE CASCADE,
        CONSTRAINT fk_menu_varian_grup_grup_id_varian_grup FOREIGN KEY(grup_id) REFERENCES varian_grup (id) ON DELETE CASCADE,
        CONSTRAINT unique_menu_varian_grup_menu_item_id_and_grup_id UNIQUE (menu_item_id, grup_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_menu_varian_grup_on_grup_id ON menu_varian_grup (grup_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS ekstra (
        id VARCHAR NOT NULL,
        nama VARCHAR(80) NOT NULL,
        harga NUMERIC(10, 2) NOT NULL,
        outlet_ids JSON,
        aktif BOOLEAN NOT NULL,
        kategori_id VARCHAR,
        urutan INTEGER NOT NULL,
        CONSTRAINT pk_ekstra PRIMARY KEY (id),
        CONSTRAINT fk_ekstra_kategori_id_kategori FOREIGN KEY(kategori_id) REFERENCES kategori (id) ON DELETE SET NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_ekstra_on_kategori_id ON ekstra (kategori_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS ekstra_harga_outlet (
        id VARCHAR NOT NULL,
        ekstra_id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        harga NUMERIC(10, 2) NOT NULL,
        CONSTRAINT pk_ekstra_harga_outlet PRIMARY KEY (id),
        CONSTRAINT fk_ekstra_harga_outlet_ekstra_id_ekstra FOREIGN KEY(ekstra_id) REFERENCES ekstra (id) ON DELETE CASCADE,
        CONSTRAINT fk_ekstra_harga_outlet_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE CASCADE,
        CONSTRAINT unique_ekstra_harga_outlet_ekstra_id_and_outlet_id UNIQUE (ekstra_id, outlet_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_ekstra_harga_outlet_on_outlet_id ON ekstra_harga_outlet (outlet_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS menu_ekstra (
        id VARCHAR NOT NULL,
        menu_item_id VARCHAR NOT NULL,
        ekstra_id VARCHAR NOT NULL,
        CONSTRAINT pk_menu_ekstra PRIMARY KEY (id),
        CONSTRAINT fk_menu_ekstra_menu_item_id_menu_items FOREIGN KEY(menu_item_id) REFERENCES menu_items (id) ON DELETE CASCADE,
        CONSTRAINT fk_menu_ekstra_ekstra_id_ekstra FOREIGN KEY(ekstra_id) REFERENCES ekstra (id) ON DELETE CASCADE,
        CONSTRAINT unique_menu_ekstra_menu_item_id_and_ekstra_id UNIQUE (menu_item_id, ekstra_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_menu_ekstra_on_ekstra_id ON menu_ekstra (ekstra_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS resep_bahan (
        id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        menu_item_id VARCHAR NOT NULL,
        bahan_id VARCHAR NOT NULL,
        katalog_id VARCHAR,
        qty NUMERIC(12, 3) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_resep_bahan PRIMARY KEY (id),
        CONSTRAINT fk_resep_bahan_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE CASCADE,
        CONSTRAINT fk_resep_bahan_menu_item_id_menu_items FOREIGN KEY(menu_item_id) REFERENCES menu_items (id) ON DELETE CASCADE,
        CONSTRAINT fk_resep_bahan_bahan_id_bahan FOREIGN KEY(bahan_id) REFERENCES bahan (id) ON DELETE CASCADE,
        CONSTRAINT fk_resep_bahan_katalog_id_katalog_bahan FOREIGN KEY(katalog_id) REFERENCES katalog_bahan (id) ON DELETE SET NULL,
        CONSTRAINT unique_resep_bahan_outlet_id_and_menu_item_id_and_bahan_id UNIQUE (outlet_id, menu_item_id, bahan_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_resep_bahan_on_menu_item_id ON resep_bahan (menu_item_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_resep_bahan_on_bahan_id ON resep_bahan (bahan_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_resep_bahan_on_katalog_id ON resep_bahan (katalog_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS resep_add_cost (
        id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        menu_item_id VARCHAR NOT NULL,
        jenis VARCHAR(10),
        nilai NUMERIC(12, 2),
        overhead NUMERIC(12, 2),
        target_margin_persen NUMERIC(5, 2),
        CONSTRAINT pk_resep_add_cost PRIMARY KEY (id),
        CONSTRAINT fk_resep_add_cost_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE CASCADE,
        CONSTRAINT fk_resep_add_cost_menu_item_id_menu_items FOREIGN KEY(menu_item_id) REFERENCES menu_items (id) ON DELETE CASCADE,
        CONSTRAINT unique_resep_add_cost_outlet_id_and_menu_item_id UNIQUE (outlet_id, menu_item_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_resep_add_cost_on_menu_item_id ON resep_add_cost (menu_item_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS ekstra_resep (
        id VARCHAR NOT NULL,
        ekstra_id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        bahan_id VARCHAR NOT NULL,
        katalog_id VARCHAR,
        qty NUMERIC(12, 3) NOT NULL,
        CONSTRAINT pk_ekstra_resep PRIMARY KEY (id),
        CONSTRAINT fk_ekstra_resep_ekstra_id_ekstra FOREIGN KEY(ekstra_id) REFERENCES ekstra (id) ON DELETE CASCADE,
        CONSTRAINT fk_ekstra_resep_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE CASCADE,
        CONSTRAINT fk_ekstra_resep_bahan_id_bahan FOREIGN KEY(bahan_id) REFERENCES bahan (id) ON DELETE CASCADE,
        CONSTRAINT fk_ekstra_resep_katalog_id_katalog_bahan FOREIGN KEY(katalog_id) REFERENCES katalog_bahan (id) ON DELETE SET NULL,
        CONSTRAINT unique_ekstra_resep_ekstra_id_and_outlet_id_and_bahan_id UNIQUE (ekstra_id, outlet_id, bahan_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_ekstra_resep_on_outlet_id ON ekstra_resep (outlet_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_ekstra_resep_on_bahan_id ON ekstra_resep (bahan_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_ekstra_resep_on_katalog_id ON ekstra_resep (katalog_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS varian_pilihan_resep (
        id VARCHAR NOT NULL,
        pilihan_id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        bahan_id VARCHAR NOT NULL,
        katalog_id VARCHAR,
        qty NUMERIC(12, 3) NOT NULL,
        CONSTRAINT pk_varian_pilihan_resep PRIMARY KEY (id),
        CONSTRAINT fk_varian_pilihan_resep_pilihan_id_varian_pilihan FOREIGN KEY(pilihan_id) REFERENCES varian_pilihan (id) ON DELETE CASCADE,
        CONSTRAINT fk_varian_pilihan_resep_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE CASCADE,
        CONSTRAINT fk_varian_pilihan_resep_bahan_id_bahan FOREIGN KEY(bahan_id) REFERENCES bahan (id) ON DELETE CASCADE,
        CONSTRAINT fk_varian_pilihan_resep_katalog_id_katalog_bahan FOREIGN KEY(katalog_id) REFERENCES katalog_bahan (id) ON DELETE SET NULL,
        CONSTRAINT unique_varian_pilihan_resep_pilihan_id_and_outlet_id_and_bahan_ UNIQUE (pilihan_id, outlet_id, bahan_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_varian_pilihan_resep_on_outlet_id ON varian_pilihan_resep (outlet_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_varian_pilihan_resep_on_bahan_id ON varian_pilihan_resep (bahan_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS index_varian_pilihan_resep_on_katalog_id ON varian_pilihan_resep (katalog_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS promo_diskon (
        id VARCHAR NOT NULL,
        nama VARCHAR(255) NOT NULL,
        deskripsi TEXT,
        jenis VARCHAR(16) NOT NULL,
        tipe_diskon VARCHAR(16) NOT NULL,
        nilai NUMERIC(12, 2) NOT NULL,
        produk_berlaku VARCHAR(500),
        produk_ids JSON,
        min_belanja NUMERIC(12, 2),
        metode_aktivasi VARCHAR(16) NOT NULL,
        tanggal_mulai DATE NOT NULL,
        tanggal_selesai DATE NOT NULL,
        aktif BOOLEAN NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_promo_diskon PRIMARY KEY (id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS promosi_cafe (
        id VARCHAR NOT NULL,
        judul VARCHAR(255) NOT NULL,
        deskripsi TEXT NOT NULL,
        gambar_url VARCHAR(1000),
        tanggal_mulai DATE NOT NULL,
        tanggal_selesai DATE NOT NULL,
        aktif BOOLEAN NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        CONSTRAINT pk_promosi_cafe PRIMARY KEY (id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS metode_bayar (
        id VARCHAR NOT NULL,
        outlet_id VARCHAR NOT NULL,
        master_id VARCHAR,
        kode VARCHAR(16) NOT NULL,
        label VARCHAR(40) NOT NULL,
        ikon VARCHAR(40) NOT NULL,
        urutan INTEGER NOT NULL,
        aktif BOOLEAN NOT NULL,
        butuh_kembalian BOOLEAN NOT NULL,
        gambar_path VARCHAR(255),
        catatan TEXT NOT NULL,
        biaya_persen NUMERIC(5, 3) NOT NULL,
        CONSTRAINT pk_metode_bayar PRIMARY KEY (id),
        CONSTRAINT fk_metode_bayar_outlet_id_outlets FOREIGN KEY(outlet_id) REFERENCES outlets (id) ON DELETE CASCADE
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS index_metode_bayar_on_outlet_id ON metode_bayar (outlet_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS item_rutin (
        id VARCHAR NOT NULL,
        nama_item VARCHAR(255) NOT NULL,
        siklus_hari INTEGER NOT NULL,
        last_purchased_at TIMESTAMP WITH TIME ZONE,
        next_due_date DATE,
        CONSTRAINT pk_item_rutin PRIMARY KEY (id)
    )
    """,
)


def upgrade() -> None:
    for statement in STATEMENTS:
        op.execute(statement)


def downgrade() -> None:
    # Irreversible by design (see the module docstring): no table is dropped.
    pass
