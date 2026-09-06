"""Database access for persisted learning evidence and mistake records."""

import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row

from agent_service.config import Settings
from agent_service.learning_models import (
    PracticeAttemptRequest,
    PracticeAttemptView,
    PracticeItemView,
)


class LearningRepository:
    """Persist Agent-owned learning artifacts while always requiring a user id."""

    def __init__(self, settings: Settings) -> None:
        self._connect = {
            "host": settings.db_host,
            "port": settings.db_port,
            "dbname": settings.db_name,
            "user": settings.db_username,
            "password": settings.db_password.get_secret_value(),
            "connect_timeout": 5,
        }

    def attachment_texts(self, user_id: UUID, attachment_ids: list[UUID]) -> list[str]:
        if not attachment_ids:
            return []
        with (
            psycopg.connect(**self._connect, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """
                SELECT extracted_text FROM learning_attachment
                WHERE user_id = %s AND id = ANY(%s) AND parse_status = 'READY'
                  AND expires_at > CURRENT_TIMESTAMP
                """,
                (user_id, attachment_ids),
            )
            return [str(row["extracted_text"]) for row in cursor.fetchall()]

    def save_attachment(
        self,
        user_id: UUID,
        original_name: str,
        media_type: str,
        relative_path: str,
        byte_size: int,
        sha256: str,
        extracted_text: str | None,
        error: str | None,
    ) -> UUID:
        attachment_id = uuid4()
        status = "READY" if extracted_text else "FAILED"
        with psycopg.connect(**self._connect) as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO learning_attachment(
                    id, user_id, original_name, media_type, relative_path, byte_size, sha256,
                    extracted_text, parse_status, parse_error, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    attachment_id,
                    user_id,
                    original_name,
                    media_type,
                    relative_path,
                    byte_size,
                    sha256,
                    extracted_text,
                    status,
                    error,
                    datetime.now(UTC) + timedelta(days=7),
                ),
            )
            connection.commit()
        return attachment_id

    def save_activity(
        self,
        user_id: UUID,
        activity_type: str,
        course: str,
        knowledge_point: str | None,
        summary: str,
        related_id: UUID | None = None,
    ) -> None:
        with psycopg.connect(**self._connect) as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO learning_activity(
                    user_id, activity_type, course, knowledge_point, summary, related_entity_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (user_id, activity_type, course, knowledge_point, summary[:4000], related_id),
            )
            connection.commit()

    def save_practices(self, user_id: UUID, items: list[dict[str, Any]]) -> list[PracticeItemView]:
        """Commit a generated set and its activity together; any failure rolls back everything."""
        with psycopg.connect(**self._connect) as connection, connection.cursor() as cursor:
            views = [self._insert_practice(user_id, item, cursor) for item in items]
            cursor.execute(
                "INSERT INTO learning_activity"
                "(user_id, activity_type, course, knowledge_point, summary) "
                "VALUES (%s, %s, %s, %s, %s)",
                (
                    user_id,
                    "PRACTICE",
                    items[0]["course"],
                    items[0]["knowledgePoint"],
                    f"生成 {len(items)} 道练习",
                ),
            )
        return views

    def _insert_practice(
        self, user_id: UUID, item: dict[str, Any], cursor: Any
    ) -> PracticeItemView:
        """Insert one item into the caller's transaction; never commit independently."""
        practice_id = uuid4()
        cursor.execute(
            """
                INSERT INTO practice_item(
                    id, user_id, course, knowledge_point, question_type, difficulty, prompt,
                    standard_answer, step_analysis, test_cases, source_type, source_label,
                    validation_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s)
                """,
            (
                practice_id,
                user_id,
                item["course"],
                item["knowledgePoint"],
                item["questionType"],
                item["difficulty"],
                item["prompt"],
                item["standardAnswer"],
                item["stepAnalysis"],
                json.dumps(item["testCases"], ensure_ascii=False),
                item["sourceType"],
                item["sourceLabel"],
                item["validationStatus"],
            ),
        )
        return PracticeItemView(id=practice_id, **item)

    def practice(self, user_id: UUID, practice_id: UUID) -> dict[str, Any] | None:
        with (
            psycopg.connect(**self._connect, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                "SELECT * FROM practice_item WHERE user_id = %s AND id = %s",
                (user_id, practice_id),
            )
            return cursor.fetchone()

    def save_attempt(
        self,
        user_id: UUID,
        request: PracticeAttemptRequest,
        practice: dict[str, Any],
        evaluation: dict[str, Any],
    ) -> PracticeAttemptView:
        attempt_id = uuid4()
        correct = bool(evaluation.get("correct"))
        score = min(100.0, max(0.0, float(evaluation.get("score", 0))))
        diagnosis = _string_list(evaluation.get("diagnosis"))
        cause = str(evaluation.get("causeType") or ("NONE" if correct else "OTHER"))[:32]
        corrected = str(evaluation.get("correctedConclusion") or practice["standard_answer"])
        suggestion = str(evaluation.get("reviewSuggestion") or "复习本题对应知识点")
        with psycopg.connect(**self._connect) as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO practice_attempt(
                    id, user_id, practice_id, work_process, final_answer, correct, score,
                    diagnosis, duration_seconds)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                """,
                (
                    attempt_id,
                    user_id,
                    request.practice_id,
                    request.work_process,
                    request.final_answer,
                    correct,
                    score,
                    json.dumps(
                        {
                            "items": diagnosis,
                            "causeType": cause,
                            "correctedConclusion": corrected,
                            "reviewSuggestion": suggestion,
                        },
                        ensure_ascii=False,
                    ),
                    request.duration_seconds,
                ),
            )
            if not correct:
                cursor.execute(
                    """
                    INSERT INTO mistake_record(
                        user_id, attempt_id, course, knowledge_point, cause_type,
                        corrected_conclusion, review_suggestion)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        attempt_id,
                        practice["course"],
                        practice["knowledge_point"],
                        cause,
                        corrected,
                        suggestion,
                    ),
                )
            # Mastery is derived from accumulated scored attempts. The model can explain
            # an error, but it cannot directly assign or overwrite this evidence score.
            cursor.execute(
                """
                INSERT INTO knowledge_mastery(
                    user_id, course, knowledge_point, mastery_score, evidence_count,
                    correct_count, last_studied_at, next_review_at)
                VALUES (%s, %s, %s, %s, 1, %s, CURRENT_TIMESTAMP,
                        CURRENT_TIMESTAMP + (%s * INTERVAL '1 day'))
                ON CONFLICT (user_id, course, knowledge_point) DO UPDATE SET
                    mastery_score = (
                        knowledge_mastery.mastery_score * knowledge_mastery.evidence_count
                        + EXCLUDED.mastery_score
                    ) / (knowledge_mastery.evidence_count + 1),
                    evidence_count = knowledge_mastery.evidence_count + 1,
                    correct_count = knowledge_mastery.correct_count + EXCLUDED.correct_count,
                    last_studied_at = CURRENT_TIMESTAMP,
                    next_review_at = EXCLUDED.next_review_at,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    user_id,
                    practice["course"],
                    practice["knowledge_point"],
                    score,
                    1 if correct else 0,
                    _next_review_days(score),
                ),
            )
            connection.commit()
        return PracticeAttemptView(
            id=attempt_id,
            practiceId=request.practice_id,
            correct=correct,
            score=score,
            diagnosis=diagnosis,
            causeType=cause,
            correctedConclusion=corrected,
            reviewSuggestion=suggestion,
        )

    def overview(self, user_id: UUID) -> dict[str, list[dict[str, Any]]]:
        with (
            psycopg.connect(**self._connect, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            queries = {
                "attempts": """
                    SELECT a.id, a.practice_id, a.work_process, a.final_answer, a.correct,
                           a.score, a.diagnosis, a.duration_seconds, a.created_at,
                           p.course, p.knowledge_point, p.prompt, p.standard_answer,
                           p.step_analysis, p.test_cases, p.source_label
                    FROM practice_attempt a JOIN practice_item p
                      ON p.id = a.practice_id AND p.user_id = a.user_id
                    WHERE a.user_id = %s ORDER BY a.created_at DESC LIMIT 100
                """,
                "activities": """
                    SELECT id, activity_type, course, knowledge_point, summary, created_at
                    FROM learning_activity WHERE user_id = %s
                    ORDER BY created_at DESC LIMIT 100
                """,
                "mistakes": """
                    SELECT m.id, m.attempt_id, m.course, m.knowledge_point, m.cause_type,
                           m.corrected_conclusion, m.review_suggestion, m.mastered, m.created_at,
                           a.work_process, a.final_answer, a.score, a.diagnosis,
                           a.duration_seconds, p.prompt, p.standard_answer, p.step_analysis,
                           p.test_cases, p.question_type, p.difficulty, p.source_type,
                           p.source_label, p.validation_status
                    FROM mistake_record m
                    JOIN practice_attempt a ON a.id = m.attempt_id AND a.user_id = m.user_id
                    JOIN practice_item p ON p.id = a.practice_id AND p.user_id = m.user_id
                    WHERE m.user_id = %s
                    ORDER BY m.mastered, m.created_at DESC LIMIT 100
                """,
                "practices": """
                    SELECT id, course, knowledge_point, question_type, difficulty, prompt,
                           standard_answer, step_analysis, test_cases, source_type, source_label,
                           validation_status, created_at
                    FROM practice_item WHERE user_id = %s
                    ORDER BY created_at DESC LIMIT 100
                """,
                "mastery": """
                    SELECT course, knowledge_point, mastery_score, evidence_count,
                           correct_count, last_studied_at, next_review_at, updated_at
                    FROM knowledge_mastery WHERE user_id = %s
                    ORDER BY mastery_score, evidence_count DESC LIMIT 100
                """,
                "weakPoints": """
                    SELECT m.course, m.knowledge_point, count(*) AS mistake_count,
                           array_agg(DISTINCT m.cause_type) AS causes,
                           max(m.created_at) AS latest_mistake_at,
                           COALESCE(k.mastery_score, 0) AS mastery_score
                    FROM mistake_record m
                    LEFT JOIN knowledge_mastery k
                      ON k.user_id = m.user_id AND k.course = m.course
                     AND k.knowledge_point = m.knowledge_point
                    WHERE m.user_id = %s AND m.mastered = FALSE
                    GROUP BY m.course, m.knowledge_point, k.mastery_score
                    ORDER BY count(*) DESC, COALESCE(k.mastery_score, 0) LIMIT 30
                """,
            }
            result: dict[str, list[dict[str, Any]]] = {}
            for name, query in queries.items():
                cursor.execute(query, (user_id,))
                result[name] = [dict(row) for row in cursor.fetchall()]
            return result

    def set_mistake_mastery(self, user_id: UUID, mistake_id: UUID, mastered: bool) -> bool:
        """Update only an owned mistake; attempt evidence remains unchanged."""

        with psycopg.connect(**self._connect) as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE mistake_record SET mastered = %s, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s AND id = %s
                """,
                (mastered, user_id, mistake_id),
            )
            return cursor.rowcount == 1


def _next_review_days(score: float) -> int:
    """Use a transparent spaced-review interval derived only from the scored attempt."""

    if score >= 85:
        return 7
    if score >= 60:
        return 3
    return 1


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
