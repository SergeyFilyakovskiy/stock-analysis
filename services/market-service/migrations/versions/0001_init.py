from alembic import op

"""
init market db

Revision ID: 0001
"""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ─────────────────────────────────────────────
    # 1. СПРАВОЧНЫЕ ТАБЛИЦЫ
    # ─────────────────────────────────────────────

    op.create_table(
        "securities",
        sa.Column("ticker",     sa.String(20),  primary_key=True),
        sa.Column("name",       sa.String(200), nullable=False),
        sa.Column("exchange",   sa.String(50)),
        sa.Column("sector",     sa.String(100)),
        sa.Column("is_active",  sa.Boolean(),   server_default=sa.true()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "market_indices",
        sa.Column("id",          sa.Integer(),   primary_key=True, autoincrement=True),
        sa.Column("index_code",  sa.String(20),  nullable=False, unique=True),
        sa.Column("name",        sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("is_active",   sa.Boolean(),   server_default=sa.true()),
    )

    op.create_table(
        "dividends",
        sa.Column("id",       sa.Integer(),      primary_key=True, autoincrement=True),
        sa.Column("ticker",   sa.String(20),     sa.ForeignKey("securities.ticker"), nullable=False),
        sa.Column("ex_date",  sa.Date(),         nullable=False),
        sa.Column("pay_date", sa.Date()),
        sa.Column("amount",   sa.Numeric(12, 6), nullable=False),
        sa.Column("currency", sa.String(3),      server_default=sa.literal("USD")),
        sa.UniqueConstraint("ticker", "ex_date", name="uq_dividends_ticker_exdate"),
    )

    op.create_index("idx_dividends_ticker_exdate", "dividends", ["ticker", sa.text("ex_date DESC")])

    # ─────────────────────────────────────────────
    # 2. ГИПЕРТАБЛИЦА
    # ─────────────────────────────────────────────

    op.create_table(
        "price_history",
        sa.Column("time",   sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("ticker", sa.String(20), sa.ForeignKey("securities.ticker"), nullable=False),
        sa.Column("open",   sa.Numeric(14, 4)),
        sa.Column("high",   sa.Numeric(14, 4)),
        sa.Column("low",    sa.Numeric(14, 4)),
        sa.Column("close",  sa.Numeric(14, 4), nullable=False),
        sa.Column("volume", sa.BigInteger()),
        sa.Column("source", sa.String(50)),
    )

    op.execute("""
        SELECT create_hypertable(
            'price_history',
            'time',
            chunk_time_interval => INTERVAL '7 days',
            if_not_exists => TRUE
        )
    """)

    op.create_index("idx_price_history_ticker_time", "price_history", ["ticker", sa.text("time DESC")])

    # ─────────────────────────────────────────────
    # 3. CONTINUOUS AGGREGATES
    # ─────────────────────────────────────────────

    op.execute("""
        CREATE MATERIALIZED VIEW ohlcv_1m
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 minute', time) AS bucket,
            ticker,
            FIRST(open,  time) AS open,
            MAX(high)          AS high,
            MIN(low)           AS low,
            LAST(close,  time) AS close,
            SUM(volume)        AS volume
        FROM price_history
        GROUP BY bucket, ticker
        WITH NO DATA
    """)

    op.execute("""
        SELECT add_continuous_aggregate_policy(
            'ohlcv_1m',
            start_offset      => INTERVAL '10 minutes',
            end_offset        => INTERVAL '1 minute',
            schedule_interval => INTERVAL '1 minute'
        )
    """)

    op.execute("""
        CREATE MATERIALIZED VIEW ohlcv_1h
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 hour', bucket) AS bucket,
            ticker,
            FIRST(open,   bucket) AS open,
            MAX(high)             AS high,
            MIN(low)              AS low,
            LAST(close,   bucket) AS close,
            SUM(volume)           AS volume
        FROM ohlcv_1m
        GROUP BY time_bucket('1 hour', bucket), ticker
        WITH NO DATA
    """)

    op.execute("""
        SELECT add_continuous_aggregate_policy(
            'ohlcv_1h',
            start_offset      => INTERVAL '2 hours',
            end_offset        => INTERVAL '1 hour',
            schedule_interval => INTERVAL '1 hour'
        )
    """)

    op.execute("""
        CREATE MATERIALIZED VIEW ohlcv_1d
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 day', bucket) AS bucket,
            ticker,
            FIRST(open,   bucket) AS open,
            MAX(high)             AS high,
            MIN(low)              AS low,
            LAST(close,   bucket) AS close,
            SUM(volume)           AS volume
        FROM ohlcv_1h
        GROUP BY time_bucket('1 day', bucket), ticker
        WITH NO DATA
    """)

    op.execute("""
        SELECT add_continuous_aggregate_policy(
            'ohlcv_1d',
            start_offset      => INTERVAL '2 days',
            end_offset        => INTERVAL '1 day',
            schedule_interval => INTERVAL '1 day'
        )
    """)

    op.execute("CREATE INDEX ON ohlcv_1m (ticker, bucket DESC)")
    op.execute("CREATE INDEX ON ohlcv_1h (ticker, bucket DESC)")
    op.execute("CREATE INDEX ON ohlcv_1d (ticker, bucket DESC)")

    # ─────────────────────────────────────────────
    # 4. СЖАТИЕ И RETENTION
    # ─────────────────────────────────────────────

    op.execute("""
        ALTER TABLE price_history SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'ticker',
            timescaledb.compress_orderby   = 'time DESC'
        )
    """)

    op.execute("SELECT add_compression_policy('price_history', INTERVAL '30 days')")
    op.execute("SELECT add_retention_policy('price_history',   INTERVAL '5 years')")


def downgrade():
    # Политики
    op.execute("SELECT remove_retention_policy('price_history',   if_exists => TRUE)")
    op.execute("SELECT remove_compression_policy('price_history', if_exists => TRUE)")

    
    op.execute("DROP MATERIALIZED VIEW IF EXISTS ohlcv_1d CASCADE")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS ohlcv_1h CASCADE")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS ohlcv_1m CASCADE")

    # Таблицы
    op.drop_table("price_history")
    op.drop_table("dividends")
    op.drop_table("market_indices")
    op.drop_table("securities")
