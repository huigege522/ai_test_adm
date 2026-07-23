"""DB fixtures — MySQL + PolarDB 连接、基准数据、adam_id 造数。"""
import os
import time
import logging
import pymysql
import pytest
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "db": os.getenv("DB_NAME", "test_db"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "charset": "utf8mb4",
    "autocommit": False,
    "cursorclass": pymysql.cursors.DictCursor,
}

POLAR_DB_CONFIG = {
    "host": os.getenv("POLAR_DB_HOST", ""),
    "port": int(os.getenv("POLAR_DB_PORT", "3306")),
    "db": os.getenv("POLAR_DB_NAME", "test_db"),
    "user": os.getenv("POLAR_DB_USER", "root"),
    "password": os.getenv("POLAR_DB_PASSWORD", ""),
    "charset": "utf8mb4",
    "autocommit": False,
    "cursorclass": pymysql.cursors.DictCursor,
} if os.getenv("POLAR_DB_HOST") else None

SQL_BASELINE = os.path.join(os.path.dirname(__file__), "..", "..", "test_data", "sql", "shared", "baseline.sql")
SQL_CLEANUP = os.path.join(os.path.dirname(__file__), "..", "..", "test_data", "sql", "shared", "cleanup.sql")


def _exec_sql_file(conn, filepath):
    if not os.path.exists(filepath):
        return
    with open(filepath, encoding="utf-8") as f:
        sql_text = f.read()
    with conn.cursor() as cur:
        for stmt in sql_text.split(";"):
            stmt = stmt.strip()
            if stmt:
                cur.execute(stmt)


# ── MySQL ───────────────────────────────────────

@pytest.fixture(scope="session")
def db_pool():
    conn = pymysql.connect(**DB_CONFIG)
    yield conn
    conn.close()


@pytest.fixture(scope="function")
def db_conn(db_pool):
    db_pool.ping(reconnect=True)
    yield db_pool
    db_pool.rollback()


@pytest.fixture(scope="function")
def db_cursor(db_conn):
    cursor = db_conn.cursor()
    yield cursor
    cursor.close()


@pytest.fixture(scope="function")
def load_baseline(db_conn):
    _exec_sql_file(db_conn, SQL_BASELINE)
    db_conn.commit()
    yield
    _exec_sql_file(db_conn, SQL_CLEANUP)
    db_conn.commit()


# ── adam_id ─────────────────────────────────────

def _adam_db_connect_config():
    if POLAR_DB_CONFIG is not None:
        return dict(POLAR_DB_CONFIG)
    return dict(DB_CONFIG)


@pytest.fixture(scope="function")
def adam_id():
    conn = None
    row_pk = None
    try:
        conn = pymysql.connect(**_adam_db_connect_config())
        adam_raw = os.getenv("FIXTURE_APP_EXT_ADAM_ID", "").strip()
        if adam_raw:
            adam_candidates = [int(adam_raw)]
        else:
            base = 798000000000000000 + (int(time.time()) % 1_000_000) * 10_000
            adam_candidates = [base + i for i in range(20)]

        full_1k_time = int(time.time())
        insert_sql = """
            INSERT INTO apple_app_ext (
              adam_id, display_status, region, new_customer_badge, full_1k_time,
              media_company_attribute, apple_direct_manager_uid, apple_direct_manager_name,
              own_genre_first, own_genre_second, own_genre_third,
              product_category, product_type, game_theme, game_play, art_style,
              attribution_type,
              creator_uid, creator_name, modifier_uid, modifier_name,
              ctime, mtime
            ) VALUES (
              %s, %s, %s, %s, %s,
              %s, %s, %s,
              %s, %s, %s,
              %s, %s, %s, %s, %s,
              %s,
              %s, %s, %s, %s,
              NOW(), NOW()
            )
        """
        params = (
            None,  # placeholder, set per attempt
            1, 1, 10, full_1k_time,
            1, 200001, "pytest-fixture",
            "手游", "RPG", "MMO", "网游", "内购", "仙侠", "副本", "国风",
            1, 10001, "pytest", 10001, "pytest",
        )

        last_err = None
        with conn.cursor() as cur:
            for adam_val in adam_candidates:
                p = (adam_val,) + params[1:]
                try:
                    cur.execute(insert_sql, p)
                    conn.commit()
                    row_pk = cur.lastrowid
                    break
                except pymysql.err.IntegrityError as e:
                    last_err = e
                    conn.rollback()
                    if adam_raw:
                        raise
                    continue
            if row_pk is None:
                raise RuntimeError("apple_app_ext 插入失败，请检查 FIXTURE_APP_EXT_ADAM_ID 或重试") from last_err

            cur.execute(
                "SELECT id, adam_id, product_category, display_status, region, full_1k_time "
                "FROM apple_app_ext WHERE id = %s",
                (row_pk,),
            )
            row = cur.fetchone()
    except Exception:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
        raise

    if not row:
        try:
            conn.close()
        except Exception:
            pass
        raise RuntimeError("adam_id fixture: 插入后查询不到 id=%s" % row_pk)

    yield row

    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM apple_app_ext WHERE id = %s", (row_pk,))
        conn.commit()
    except Exception:
        logger.exception("adam_id fixture: 清理删除失败 id=%s", row_pk)
    finally:
        try:
            conn.close()
        except Exception:
            pass


# ── PolarDB ─────────────────────────────────────

@pytest.fixture(scope="session")
def polar_db_pool():
    if POLAR_DB_CONFIG is None:
        pytest.skip("未配置 POLAR_DB_HOST，跳过需要 PolarDB 的用例")
    conn = pymysql.connect(**POLAR_DB_CONFIG)
    yield conn
    conn.close()


@pytest.fixture(scope="function")
def polar_db_conn(polar_db_pool):
    polar_db_pool.ping(reconnect=True)
    yield polar_db_pool
    polar_db_pool.rollback()


@pytest.fixture(scope="function")
def polar_db_cursor(polar_db_conn):
    cursor = polar_db_conn.cursor()
    yield cursor
    cursor.close()
