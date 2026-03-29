"""
tracker.py — PostgreSQL (Neon) tracking logic for FOIA/RTI Request Generator.

Manages the request tracking database using Neon serverless PostgreSQL.
Provides functions to initialize the database, save requests, list all
tracked requests, and update request statuses.
"""

import os
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv(Path(__file__).resolve().parent / ".env")


def _get_connection():
    """
    Get a PostgreSQL connection using the DATABASE_URL from environment.

    Returns:
        psycopg2 connection object.

    Raises:
        RuntimeError: If DATABASE_URL is not configured.
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. "
            "Please configure it in your .env file. "
            "Example: DATABASE_URL=postgresql://user:pass@host/dbname?sslmode=require"
        )
    return psycopg2.connect(database_url)


def init_db():
    """
    Initialize the requests table in Neon PostgreSQL if it doesn't exist.

    Creates the table with the schema defined in TRD §3.3.
    """
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS requests (
                    id              TEXT PRIMARY KEY,
                    agency_key      TEXT NOT NULL,
                    agency_name     TEXT NOT NULL,
                    jurisdiction    TEXT NOT NULL,
                    subject         TEXT NOT NULL,
                    requester_name  TEXT NOT NULL,
                    date_sent       TEXT NOT NULL,
                    response_due    TEXT NOT NULL,
                    status          TEXT DEFAULT 'SENT',
                    output_file     TEXT,
                    n8n_notified    INTEGER DEFAULT 0,
                    created_at      TIMESTAMPTZ DEFAULT NOW()
                );
            """)
        conn.commit()
    finally:
        conn.close()


def save_request(
    request_id: str,
    agency_key: str,
    agency_name: str,
    jurisdiction: str,
    subject: str,
    requester_name: str,
    date_sent: str,
    response_due: str,
    output_file: str,
):
    """
    Save a new request record to the database.

    Args:
        request_id: Unique request ID (e.g., FOIA-2025-A7F3C2D1).
        agency_key: Agency shortcode (e.g., USDA).
        agency_name: Full agency name.
        jurisdiction: Jurisdiction key (e.g., federal).
        subject: First 100 chars of the records description.
        requester_name: Name of the requester.
        date_sent: ISO date string (YYYY-MM-DD).
        response_due: ISO date string (YYYY-MM-DD).
        output_file: Path to the saved output file.
    """
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO requests
                    (id, agency_key, agency_name, jurisdiction, subject,
                     requester_name, date_sent, response_due, output_file)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    request_id,
                    agency_key,
                    agency_name,
                    jurisdiction,
                    subject[:100],
                    requester_name,
                    date_sent,
                    response_due,
                    output_file,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def list_requests() -> list:
    """
    Retrieve all tracked requests from the database.

    Returns:
        List of dicts, each representing a request row.
    """
    conn = _get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, agency_key, agency_name, jurisdiction, subject, "
                "requester_name, date_sent, response_due, status, output_file, "
                "n8n_notified, created_at "
                "FROM requests ORDER BY created_at DESC"
            )
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    finally:
        conn.close()


def update_status(request_id: str, new_status: str) -> bool:
    """
    Update the status of an existing request.

    Args:
        request_id: The unique request ID to update.
        new_status: New status value (SENT, RESPONDED, OVERDUE, CLOSED).

    Returns:
        True if a row was updated, False if request_id not found.
    """
    valid_statuses = {"SENT", "RESPONDED", "OVERDUE", "CLOSED", "FOLLOWED_UP"}
    if new_status.upper() not in valid_statuses:
        raise ValueError(
            f"Invalid status: '{new_status}'. "
            f"Valid statuses: {', '.join(sorted(valid_statuses))}"
        )

    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE requests SET status = %s WHERE id = %s",
                (new_status.upper(), request_id),
            )
            updated = cur.rowcount > 0
        conn.commit()
        return updated
    finally:
        conn.close()


def mark_n8n_notified(request_id: str):
    """
    Mark a request as having been notified via n8n webhook.

    Args:
        request_id: The unique request ID to mark.
    """
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE requests SET n8n_notified = 1 WHERE id = %s",
                (request_id,),
            )
        conn.commit()
    finally:
        conn.close()
