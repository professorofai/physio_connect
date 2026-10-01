import click
from flask import current_app
from sqlalchemy import inspect, text

from app.extensions import db


EXPECTED_TABLES = {
    "users",
    "otp_verifications",
    "physio_profiles",
    "appointments",
}
EXPECTED_CONSTRAINTS = {
    "uq_user_email",
    "uq_user_phone_number",
    "uq_physio_profile_user",
    "ck_appointments_status",
    "uq_appointments_physio_slot",
}


def _ensure_appointment_slot_constraint(connection):
    constraint_exists = connection.execute(
        text("""
            SELECT 1
            FROM pg_constraint
            WHERE conrelid = 'public.appointments'::regclass
              AND conname = 'uq_appointments_physio_slot'
        """)
    ).scalar()
    if constraint_exists:
        return False

    duplicate = connection.execute(
        text("""
            SELECT physio_id, appointment_date, appointment_time
            FROM appointments
            GROUP BY physio_id, appointment_date, appointment_time
            HAVING COUNT(*) > 1
            LIMIT 1
        """)
    ).first()
    if duplicate:
        raise RuntimeError(
            "Cannot add appointment slot constraint because duplicate data exists: "
            f"{duplicate}"
        )

    connection.execute(text("""
        ALTER TABLE appointments
        ADD CONSTRAINT uq_appointments_physio_slot
        UNIQUE (physio_id, appointment_date, appointment_time)
    """))
    return True


def _require_postgresql():
    database_url = current_app.config.get("SQLALCHEMY_DATABASE_URI")
    if not database_url:
        raise click.ClickException("DATABASE_URL is not configured.")
    if not database_url.lower().startswith(("postgresql://", "postgresql+", "postgres://")):
        raise click.ClickException("DATABASE_URL must point to PostgreSQL.")


def _schema_report(connection):
    inspector = inspect(connection)
    tables = set(inspector.get_table_names(schema="public"))
    constraints = set()
    for table_name in EXPECTED_TABLES & tables:
        for constraint in inspector.get_unique_constraints(table_name):
            if constraint.get("name"):
                constraints.add(constraint["name"])
        for constraint in inspector.get_check_constraints(table_name):
            if constraint.get("name"):
                constraints.add(constraint["name"])

    foreign_keys = set()
    for table_name in EXPECTED_TABLES & tables:
        foreign_keys.update(
            (
                table_name,
                foreign_key["constrained_columns"][0],
                foreign_key["referred_table"],
                foreign_key["referred_columns"][0],
            )
            for foreign_key in inspector.get_foreign_keys(table_name)
        )
    expected_foreign_keys = {
        ("appointments", "patient_id", "users", "id"),
        ("appointments", "physio_id", "physio_profiles", "id"),
        ("physio_profiles", "user_id", "users", "id"),
    }
    return tables, constraints, foreign_keys, expected_foreign_keys


def register_database_commands(app):
    @app.cli.group("db")
    def database_commands():
        """Explicit, non-destructive PostgreSQL database operations."""

    @database_commands.command("init")
    def init_database():
        """Create missing application tables without dropping data."""
        _require_postgresql()
        try:
            with db.engine.begin() as connection:
                database_name = connection.execute(
                    text("SELECT current_database()")
                ).scalar_one()
                existing_tables = set(inspect(connection).get_table_names(schema="public"))
                db.metadata.create_all(bind=connection, checkfirst=True)
                connection.execute(
                    text("ALTER TABLE users ADD COLUMN IF NOT EXISTS age INTEGER")
                )
                connection.execute(
                    text("ALTER TABLE users ALTER COLUMN phone_number DROP NOT NULL")
                )
                connection.execute(
                    text("ALTER TABLE users ALTER COLUMN city DROP NOT NULL")
                )
                constraint_created = _ensure_appointment_slot_constraint(connection)
                created_tables = EXPECTED_TABLES - existing_tables
        except Exception as exc:
            raise click.ClickException(f"Database initialization failed: {exc}") from exc

        click.echo(f"Connected to PostgreSQL database: {database_name}")
        if created_tables:
            click.echo(f"Created tables: {', '.join(sorted(created_tables))}")
        else:
            click.echo("Schema already exists; no tables were created.")
        if constraint_created:
            click.echo("Created constraint: uq_appointments_physio_slot")

    @database_commands.command("verify")
    def verify_database():
        """Verify the PostgreSQL connection and expected application schema."""
        _require_postgresql()
        try:
            with db.engine.connect() as connection:
                database_name = connection.execute(
                    text("SELECT current_database()")
                ).scalar_one()
                tables, constraints, foreign_keys, expected_foreign_keys = _schema_report(
                    connection
                )
        except Exception as exc:
            raise click.ClickException(f"Database verification failed: {exc}") from exc

        missing_tables = EXPECTED_TABLES - tables
        extra_tables = tables - EXPECTED_TABLES - {"alembic_version"}
        missing_constraints = EXPECTED_CONSTRAINTS - constraints
        missing_foreign_keys = expected_foreign_keys - foreign_keys

        click.echo(f"Connected to PostgreSQL database: {database_name}")
        click.echo(f"Application tables: {', '.join(sorted(tables & EXPECTED_TABLES)) or 'none'}")
        click.echo(f"Constraints verified: {', '.join(sorted(EXPECTED_CONSTRAINTS & constraints)) or 'none'}")
        click.echo(f"Foreign keys verified: {len(expected_foreign_keys - missing_foreign_keys)}/3")
        if missing_tables or extra_tables or missing_constraints or missing_foreign_keys:
            problems = []
            if missing_tables:
                problems.append(f"missing tables: {', '.join(sorted(missing_tables))}")
            if extra_tables:
                problems.append(f"unexpected tables: {', '.join(sorted(extra_tables))}")
            if missing_constraints:
                problems.append(f"missing constraints: {', '.join(sorted(missing_constraints))}")
            if missing_foreign_keys:
                formatted_foreign_keys = ", ".join(
                    f"{table}.{column} -> {referred_table}.{referred_column}"
                    for table, column, referred_table, referred_column in sorted(
                        missing_foreign_keys
                    )
                )
                problems.append(f"missing foreign keys: {formatted_foreign_keys}")
            raise click.ClickException("Schema verification failed: " + "; ".join(problems))
        click.echo("Schema verification passed.")