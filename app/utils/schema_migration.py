from sqlalchemy import inspect, text

from app.extensions import db


def _table_has_column(connection, table_name, column_name):
    inspector = inspect(connection)
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _add_column_if_missing(connection, table_name, column_sql):
    if not _table_has_column(connection, table_name, column_sql.split()[0]):
        connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}"))


def _has_unique_constraint(connection, table_name, constraint_name):
    inspector = inspect(connection)
    return any(constraint.get("name") == constraint_name for constraint in inspector.get_unique_constraints(table_name))


def _rebuild_table(connection, table_name, create_sql, insert_sql):
    backup_name = f"{table_name}_backup"
    connection.execute(text(f"DROP TABLE IF EXISTS {backup_name}"))
    connection.execute(text(f"ALTER TABLE {table_name} RENAME TO {backup_name}"))
    connection.execute(text(create_sql))
    connection.execute(text(insert_sql))
    connection.execute(text(f"DROP TABLE {backup_name}"))


def ensure_database_schema():
    with db.engine.begin() as connection:
        connection.execute(text("PRAGMA foreign_keys = OFF"))

        if not inspect(connection).has_table("user"):
            db.create_all()
            connection.execute(text("PRAGMA foreign_keys = ON"))
            return

        if not _table_has_column(connection, "user", "created_at"):
            _add_column_if_missing(connection, "user", "created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
        if not _table_has_column(connection, "user", "updated_at"):
            _add_column_if_missing(connection, "user", "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
        if not _table_has_column(connection, "user", "phone_number"):
            _add_column_if_missing(connection, "user", "phone_number VARCHAR(15)")
        if not _table_has_column(connection, "user", "city"):
            _add_column_if_missing(connection, "user", "city VARCHAR(100)")
        if not _table_has_column(connection, "user", "is_verified"):
            _add_column_if_missing(connection, "user", "is_verified BOOLEAN DEFAULT 0")
        if not _table_has_column(connection, "user", "profile_picture"):
            _add_column_if_missing(connection, "user", "profile_picture VARCHAR(200)")

        if not _table_has_column(connection, "physio_profile", "created_at"):
            _add_column_if_missing(connection, "physio_profile", "created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
        if not _table_has_column(connection, "physio_profile", "updated_at"):
            _add_column_if_missing(connection, "physio_profile", "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
        if not _table_has_column(connection, "physio_profile", "certificates"):
            _add_column_if_missing(connection, "physio_profile", "certificates VARCHAR(500)")

        if not _table_has_column(connection, "appointment", "created_at"):
            _add_column_if_missing(connection, "appointment", "created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
        if not _table_has_column(connection, "appointment", "appointment_time"):
            _add_column_if_missing(connection, "appointment", "appointment_time TIME")
        if not _table_has_column(connection, "appointment", "duration_minutes"):
            _add_column_if_missing(connection, "appointment", "duration_minutes INTEGER DEFAULT 30")
        if not _table_has_column(connection, "appointment", "updated_at"):
            _add_column_if_missing(connection, "appointment", "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")

        if not _table_has_column(connection, "otp_verification", "updated_at"):
            _add_column_if_missing(connection, "otp_verification", "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")

        # Rebuild tables when unique constraints or non-null constraints need to be enforced.
        if inspect(connection).has_table("user") and not _has_unique_constraint(connection, "user", "uq_user_email"):
            _rebuild_table(
                connection,
                "user",
                """
                CREATE TABLE user (
                    id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    phone_number VARCHAR(15) NOT NULL,
                    city VARCHAR(100) NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL DEFAULT 'patient',
                    is_verified BOOLEAN NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (id),
                    UNIQUE (email),
                    UNIQUE (phone_number)
                )
                """,
                """
                INSERT INTO user (id, name, email, phone_number, city, password, role, is_verified, created_at, updated_at)
                SELECT id, name, COALESCE(email, ''), COALESCE(phone_number, ''), COALESCE(city, ''), password, COALESCE(role, 'patient'), COALESCE(is_verified, 0), COALESCE(created_at, CURRENT_TIMESTAMP), COALESCE(updated_at, CURRENT_TIMESTAMP) FROM user_backup
                """,
            )

        if inspect(connection).has_table("physio_profile") and not _has_unique_constraint(connection, "physio_profile", "uq_physio_profile_user"):
            _rebuild_table(
                connection,
                "physio_profile",
                """
                CREATE TABLE physio_profile (
                    id INTEGER NOT NULL,
                    clinic_name VARCHAR(200) NOT NULL,
                    location VARCHAR(200) NOT NULL,
                    specialization VARCHAR(200) NOT NULL,
                    experience INTEGER DEFAULT 0,
                    profile_picture VARCHAR(200),
                    user_id INTEGER NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (id),
                    FOREIGN KEY(user_id) REFERENCES user (id) ON DELETE CASCADE,
                    UNIQUE (user_id)
                )
                """,
                """
                INSERT INTO physio_profile (id, clinic_name, location, specialization, experience, profile_picture, user_id, created_at, updated_at)
                SELECT id, clinic_name, location, specialization, experience, profile_picture, user_id, COALESCE(created_at, CURRENT_TIMESTAMP), COALESCE(updated_at, CURRENT_TIMESTAMP) FROM physio_profile_backup
                """,
            )

        if inspect(connection).has_table("appointment") and not _table_has_column(connection, "appointment", "updated_at"):
            _rebuild_table(
                connection,
                "appointment",
                """
                CREATE TABLE appointment (
                    id INTEGER NOT NULL,
                    patient_id INTEGER NOT NULL,
                    physio_id INTEGER NOT NULL,
                    appointment_date VARCHAR(50) NOT NULL,
                    appointment_time TIME,
                    duration_minutes INTEGER NOT NULL DEFAULT 30,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (id),
                    FOREIGN KEY(patient_id) REFERENCES user (id) ON DELETE CASCADE,
                    FOREIGN KEY(physio_id) REFERENCES physio_profile (id) ON DELETE CASCADE
                )
                """,
                """
                INSERT INTO appointment (id, patient_id, physio_id, appointment_date, appointment_time, duration_minutes, status, created_at, updated_at)
                SELECT id, patient_id, physio_id, appointment_date, appointment_time, COALESCE(duration_minutes, 30), COALESCE(status, 'pending'), COALESCE(created_at, CURRENT_TIMESTAMP), COALESCE(updated_at, CURRENT_TIMESTAMP) FROM appointment_backup
                """,
            )

        if inspect(connection).has_table("otp_verification") and not _table_has_column(connection, "otp_verification", "updated_at"):
            _rebuild_table(
                connection,
                "otp_verification",
                """
                CREATE TABLE otp_verification (
                    id INTEGER NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    otp_code VARCHAR(6) NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL,
                    is_used BOOLEAN NOT NULL DEFAULT 0,
                    PRIMARY KEY (id)
                )
                """,
                """
                INSERT INTO otp_verification (id, email, otp_code, created_at, updated_at, expires_at, is_used)
                SELECT id, email, otp_code, COALESCE(created_at, CURRENT_TIMESTAMP), COALESCE(updated_at, CURRENT_TIMESTAMP), expires_at, COALESCE(is_used, 0) FROM otp_verification_backup
                """,
            )

        connection.execute(text("PRAGMA foreign_keys = ON"))
