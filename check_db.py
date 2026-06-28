# ============================================================
# CONFIG — change this one line to switch between DBs
# ============================================================
DB_TYPE = "remote"   # "remote" = Postgres (Render), "local" = SQLite


POSTGRES_URL = "postgresql://orderr_db_user:VORCj0qqoRQZO3H7fGwurX4EBLPr0ww1@dpg-d881pu1kh4rs73c969f0-a.singapore-postgres.render.com/orderr_db"

SQLITE_PATH = "C:/Imp Data/Personal/OrdeRR/orderr.db"
# ============================================================



if DB_TYPE == "remote":
    import psycopg2
    conn = psycopg2.connect(POSTGRES_URL, sslmode="require")
elif DB_TYPE == "local":
    import sqlite3
    conn = sqlite3.connect(SQLITE_PATH)
else:
    raise ValueError("DB_TYPE must be 'remote' or 'local'")

cur = conn.cursor()


def adapt(query):
    """Postgres uses %s placeholders, SQLite uses ?. Auto-convert."""
    return query.replace("%s", "?") if DB_TYPE == "local" else query


def run(title, query, params=None):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print("=" * 70)
    try:
        cur.execute(adapt(query), params or ())
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        print(" | ".join(cols))
        print("-" * 70)
        for row in rows:
            print(" | ".join(str(v) if v is not None else "NULL" for v in row))
        print(f"  ({len(rows)} rows)")
    except Exception as e:
        print(f"ERROR: {e}")
        conn.rollback()


def run_write(title, query, params=None):
    """For INSERT/UPDATE/DELETE — commits and prints rows affected."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print("=" * 70)
    try:
        cur.execute(adapt(query), params or ())
        conn.commit()
        print(f"  ✅ Done. Rows affected: {cur.rowcount}")
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        conn.rollback()


def truncate_tables(tables):
    """
    Delete all rows from the given tables and reset auto-increment IDs.
    Postgres: TRUNCATE ... RESTART IDENTITY CASCADE
    SQLite:   DELETE FROM each table + reset sqlite_sequence
    """
    title = f"Delete all rows from: {', '.join(tables)}"
    print(f"\n{'='*70}")
    print(f"  {title}")
    print("=" * 70)
    try:
        if DB_TYPE == "remote":
            cur.execute(f"TRUNCATE {', '.join(tables)} RESTART IDENTITY CASCADE;")
        else:
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence';"
            )
            has_seq_table = cur.fetchone() is not None
            for t in tables:
                cur.execute(f"DELETE FROM {t};")
                if has_seq_table:
                    cur.execute("DELETE FROM sqlite_sequence WHERE name = ?;", (t,))
        conn.commit()
        print("  ✅ Done.")
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        conn.rollback()


# ============================================================
# QUICK-REFERENCE — billing tables
# ============================================================
#
#   order_item_actuals      — delivered quantities captured from photo OCR or manual entry
#   ocr_unmatched_lines     — OCR lines that couldn't be matched to a product (review queue)
#   invoices                — generated invoice headers
#   invoice_items           — line items for each invoice (cols: rate_used, amount, rate_source)
#   customer_rate_overrides — per-customer price overrides with effective date ranges
#
# ============================================================


# ============================================================
# INSPECTION QUERIES — uncomment the block(s) you need
# ============================================================

# ── All tables, recent rows ──────────────────────────────────────────────────

# run("order_item_actuals (latest 30)",
#     """
#     SELECT id, order_id, product, ordered_quantity, ordered_unit,
#            actual_quantity, actual_unit, capture_source, confidence,
#            confirmed_by, confirmed_at
#     FROM order_item_actuals
#     ORDER BY id DESC LIMIT 30;
#     """)

# run("ocr_unmatched_lines (unresolved)",
#     """
#     SELECT id, order_id, raw_line, reason, resolved
#     FROM ocr_unmatched_lines
#     WHERE resolved = false
#     ORDER BY id DESC LIMIT 30;
#     """)

# run("invoices (latest 20)",
#     """
#     SELECT id, invoice_number, order_id, customer_phone,
#            business_date, total, status, created_at
#     FROM invoices
#     ORDER BY id DESC LIMIT 20;
#     """)

# run("invoice_items (latest 30)",
#     """
#     SELECT ii.id, ii.invoice_id, i.invoice_number, ii.product,
#            ii.quantity, ii.unit, ii.rate_used, ii.amount, ii.rate_source
#     FROM invoice_items ii
#     JOIN invoices i ON i.id = ii.invoice_id
#     ORDER BY ii.id DESC LIMIT 30;
#     """)

# run("customer_rate_overrides (all active)",
#     """
#     SELECT id, customer_phone, product, rate_per_unit, unit,
#            effective_from, effective_to
#     FROM customer_rate_overrides
#     WHERE effective_to IS NULL OR effective_to >= CURRENT_DATE
#     ORDER BY customer_phone, product, effective_from DESC;
#     """)
run("All tables in public schema",
    """
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name;
    """)

run("Columns in customers table",
    """
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'customers'
    ORDER BY ordinal_position;
    """)

run("Sample customers rows",
    """
    SELECT * FROM customers LIMIT 5;
    """)

# ── Targeted inspection ──────────────────────────────────────────────────────

# Actuals for a specific order
# run("Actuals for order 123",
#     "SELECT * FROM order_item_actuals WHERE order_id = %s ORDER BY id;",
#     (123,))

# All unmatched lines for a specific order
# run("Unmatched lines for order 123",
#     "SELECT * FROM ocr_unmatched_lines WHERE order_id = %s ORDER BY id;",
#     (123,))

# Full invoice with line items
# run("Invoice detail — invoice_id 5",
#     """
#     SELECT i.invoice_number, i.customer_phone, i.business_date, i.total,
#            ii.product, ii.quantity, ii.unit, ii.rate_used, ii.amount, ii.rate_source
#     FROM invoices i
#     JOIN invoice_items ii ON ii.invoice_id = i.id
#     WHERE i.id = %s
#     ORDER BY ii.id;
#     """, (5,))

# All invoices for a customer
# run("Invoices for customer 919876543210",
#     "SELECT * FROM invoices WHERE customer_phone = %s ORDER BY business_date DESC;",
#     ("919876543210",))

# Needs-review actuals across all orders
# run("All needs-review actuals",
#     """
#     SELECT id, order_id, product, actual_quantity, unit, capture_source, confirmed_by
#     FROM order_item_actuals
#     WHERE confidence = 'needs_review'
#     ORDER BY order_id, id;
#     """)


# ============================================================
# WRITE OPERATIONS — uncomment the one you need, run, re-comment
# ============================================================

# ── Clean up bad OCR run for a specific order ────────────────────────────────
# (Use this after the Vision→Gemini migration to clear broken lines)

# run_write(
#     "Delete unresolved unmatched lines for order 1",
#     "DELETE FROM ocr_unmatched_lines WHERE order_id = %s AND resolved = false;",
#     (1,)
# )

# run_write(
#     "Delete photo_ocr actuals for order 1 (so re-upload starts fresh)",
#     "DELETE FROM order_item_actuals WHERE order_id = %s AND capture_source = 'photo_ocr';",
#     (1,)
# )

# ── Soft-delete a rate override (sets effective_to = today) ─────────────────
# run_write(
#     "Deactivate rate override id 7",
#     "UPDATE customer_rate_overrides SET effective_to = CURRENT_DATE WHERE id = %s;",
#     (7,)
# )

# ── Void an invoice (set status = 'voided') ──────────────────────────────────
# run_write(
#     "Void invoice id 5",
#     "UPDATE invoices SET status = 'voided' WHERE id = %s;",
#     (5,)
# )

# ── Manually confirm a needs_review actual ───────────────────────────────────
# run_write(
#     "Confirm actual id 42 (set quantity + mark confirmed)",
#     """
#     UPDATE order_item_actuals
#     SET actual_quantity = %s,
#         confidence      = 'auto',
#         confirmed_by    = %s,
#         confirmed_at    = NOW()
#     WHERE id = %s;
#     """,
#     (9.5, "admin", 42)
# )

#── Nuclear option — clear ALL billing data (keeps schema intact) ─────────────
truncate_tables([
    "invoice_items",
    "invoices",
    "ocr_unmatched_lines",
    "order_item_actuals",
    "customer_rate_overrides",
])


cur.close()
conn.close()
print("\n✅ Done.")