"""Export only course-index tables; import into a migrated, empty local index.

This is deliberately not a whole-database dump: no account, session, conversation,
attachment, exam or learner history table can enter the archive. Environment
variables supply connection secrets; they are never serialized or printed.
"""

import argparse
import gzip
import json
import os
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

COURSES = {"数据结构", "算法设计与分析", "计算机网络"}
TABLES = {
    "study_material": (
        "id course relative_path file_type byte_size modified_at sha256 parse_status "
        "parser_version active indexed_at created_at updated_at"
    ).split(),
    "study_material_chunk": (
        "id material_id chunk_index locator content content_hash embedding"
    ).split(),
}


def connect():
    """Use the teammate's local connection settings, never values from the archive."""
    return psycopg.connect(
        host=os.environ["SCHOOL_AGENT_DB_HOST"],
        port=os.environ["SCHOOL_AGENT_DB_PORT"],
        dbname=os.environ["SCHOOL_AGENT_DB_NAME"],
        user=os.environ["SCHOOL_AGENT_DB_USERNAME"],
        password=os.environ["SCHOOL_AGENT_DB_PASSWORD"],
        connect_timeout=10,
        row_factory=dict_row,
    )


def export_index(path):
    """Export an explicit column/table/course allowlist, not arbitrary database rows."""
    result = {"format": "m06-course-index-v1", "tables": {}}
    with connect() as connection:
        for table, columns in TABLES.items():
            where = (
                "course = ANY(%s) AND active AND parse_status = 'INDEXED'"
                if table == "study_material"
                else "material_id IN (SELECT id FROM study_material WHERE "
                "course = ANY(%s) AND active AND parse_status = 'INDEXED')"
            )
            query = sql.SQL("SELECT {} FROM {} WHERE " + where + " ORDER BY id").format(
                sql.SQL(", ").join(map(sql.Identifier, columns)), sql.Identifier(table)
            )
            result["tables"][table] = connection.execute(
                query, (sorted(COURSES),)
            ).fetchall()
    validate(result)
    if path.exists():
        raise ValueError("Archive already exists; choose a new export path")
    path.parent.mkdir(parents=True, exist_ok=True)
    # This generated artifact contains only the allowlisted shared curriculum index.
    with gzip.open(path, "wt", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, default=str)
    return result


def validate(data):
    """Reject unexpected tables/columns and paths outside the three course folders."""
    if data.get("format") != "m06-course-index-v1" or set(data["tables"]) != set(
        TABLES
    ):
        raise ValueError("Unexpected archive format or table")
    for table, columns in TABLES.items():
        if not isinstance(data["tables"][table], list):
            raise ValueError("Expected a row list")
        for row in data["tables"][table]:
            if set(row) != set(columns):
                raise ValueError("Unexpected columns")
    ids = {str(row["id"]) for row in data["tables"]["study_material"]}
    for row in data["tables"]["study_material"]:
        parts = row["relative_path"].replace("\\", "/").split("/")
        if row["course"] not in COURSES or parts[0] != row["course"] or ".." in parts:
            raise ValueError("Material outside allowed courses")
    for row in data["tables"]["study_material_chunk"]:
        if str(row["material_id"]) not in ids:
            raise ValueError("Orphaned material chunk")


def import_index(path):
    """Restore atomically; refuse to overwrite an existing index or learning data."""
    with gzip.open(path, "rb") as stream:
        payload = stream.read(128 * 1024 * 1024 + 1)
    if len(payload) > 128 * 1024 * 1024:
        raise ValueError("Expanded archive exceeds 128 MiB")
    data = json.loads(payload)
    validate(data)
    with connect() as connection:
        connection.execute(
            "LOCK TABLE study_material, study_material_chunk IN EXCLUSIVE MODE"
        )
        for table in TABLES:
            if connection.execute(
                sql.SQL("SELECT 1 FROM {} LIMIT 1").format(sql.Identifier(table))
            ).fetchone():
                raise ValueError(
                    "Index is not empty; import refused without changing any rows"
                )
        with connection.cursor() as cursor:
            for table, columns in TABLES.items():
                query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                    sql.Identifier(table),
                    sql.SQL(", ").join(map(sql.Identifier, columns)),
                    sql.SQL(", ").join(sql.Placeholder() for _ in columns),
                )
                cursor.executemany(
                    query,
                    [
                        [row[column] for column in columns]
                        for row in data["tables"][table]
                    ],
                )
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["export", "import"])
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    data = (
        export_index(args.archive)
        if args.operation == "export"
        else import_index(args.archive)
    )
    print(
        json.dumps(
            {
                "operation": args.operation,
                "rows": {name: len(rows) for name, rows in data["tables"].items()},
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
