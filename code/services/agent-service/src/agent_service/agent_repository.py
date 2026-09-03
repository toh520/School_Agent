"""PostgreSQL persistence for Agent-owned conversations, traces, versions, and feedback."""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row

from agent_service.agent_models import (
    ConversationDetail,
    ConversationSummary,
    FeedbackCreate,
    IdentityContext,
    Intent,
    MessageView,
    PersistedTurn,
    ToolCallTrace,
    WorkflowResult,
)
from agent_service.config import Settings


class AgentRecordNotFound(RuntimeError):
    """Raised when a record does not exist or belongs to a different student."""


class AgentRepository:
    """Own M04 tables while leaving Java-owned business facts untouched."""

    def __init__(self, settings: Settings) -> None:
        self._connect = {
            "host": settings.db_host,
            "port": settings.db_port,
            "dbname": settings.db_name,
            "user": settings.db_username,
            "password": settings.db_password.get_secret_value(),
            "connect_timeout": 3,
        }

    @contextmanager
    def _connection(self) -> Iterator[psycopg.Connection[dict[str, Any]]]:
        with psycopg.connect(**self._connect, row_factory=dict_row) as connection:
            yield connection

    def llm_runtime_config(self) -> dict[str, Any]:
        """Return the active non-secret LLM overrides maintained by administrators."""

        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT payload->>'configValue' AS config_value
                FROM system_config
                WHERE lower(code) = lower('LLM_RUNTIME')
                  AND status = 'ACTIVE' AND deleted_at IS NULL
                ORDER BY updated_at DESC
                LIMIT 1
                """
            )
            row = cursor.fetchone()
        if row is None or not row.get("config_value"):
            return {}
        try:
            value = json.loads(str(row["config_value"]))
            return value if isinstance(value, dict) else {}
        except json.JSONDecodeError:
            return {}

    def create_conversation(self, user_id: UUID, title: str) -> ConversationSummary:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO agent_conversation(id, user_id, title)
                VALUES (%s, %s, %s)
                RETURNING id, title, current_intent, updated_at
                """,
                (uuid4(), user_id, title),
            )
            return self._summary(cursor.fetchone())

    def list_conversations(self, user_id: UUID) -> list[ConversationSummary]:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, title, current_intent, updated_at
                FROM agent_conversation
                WHERE user_id = %s AND status = 'ACTIVE'
                ORDER BY updated_at DESC
                """,
                (user_id,),
            )
            return [self._summary(row) for row in cursor.fetchall()]

    def conversation(self, user_id: UUID, conversation_id: UUID) -> ConversationDetail:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, title, current_intent, updated_at
                FROM agent_conversation
                WHERE id = %s AND user_id = %s AND status = 'ACTIVE'
                """,
                (conversation_id, user_id),
            )
            row = cursor.fetchone()
            if row is None:
                raise AgentRecordNotFound("CONVERSATION_NOT_FOUND")
            cursor.execute(
                """
                SELECT message.id, message.role, message.content, message.sequence_number,
                       result.id AS result_version_id, task.id AS task_id, task.intent,
                       COALESCE(result.fallback_used, FALSE) AS fallback_used,
                       COALESCE(result.basis, '[]'::jsonb) AS basis,
                       COALESCE(result.limitations, '[]'::jsonb) AS limitations,
                       message.created_at
                FROM agent_message message
                LEFT JOIN agent_result_version result ON result.assistant_message_id = message.id
                LEFT JOIN agent_task task ON task.id = result.task_id
                WHERE message.conversation_id = %s
                ORDER BY message.sequence_number
                """,
                (conversation_id,),
            )
            messages = [self._message(item) for item in cursor.fetchall()]
            summary = self._summary(row)
            return ConversationDetail(**summary.model_dump(), messages=messages)

    def delete_conversation(self, user_id: UUID, conversation_id: UUID) -> None:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE agent_conversation
                SET status = 'DELETED', deleted_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND user_id = %s AND status = 'ACTIVE'
                """,
                (conversation_id, user_id),
            )
            if cursor.rowcount != 1:
                raise AgentRecordNotFound("CONVERSATION_NOT_FOUND")

    def start_turn(
        self, user_id: UUID, conversation_id: UUID, content: str, request_id: str
    ) -> tuple[UUID, UUID]:
        """Lock the conversation so concurrent messages cannot reuse a sequence number."""

        message_id, task_id = uuid4(), uuid4()
        with self._connection() as connection, connection.cursor() as cursor:
            self._lock_owned_conversation(cursor, user_id, conversation_id)
            sequence = self._next_sequence(cursor, conversation_id)
            cursor.execute(
                """
                INSERT INTO agent_message(id, conversation_id, role, content, sequence_number)
                VALUES (%s, %s, 'USER', %s, %s)
                """,
                (message_id, conversation_id, content, sequence),
            )
            cursor.execute(
                """
                INSERT INTO agent_task(
                    id, conversation_id, user_message_id, intent, status, request_id)
                VALUES (%s, %s, %s, 'UNKNOWN', 'RUNNING', %s)
                """,
                (task_id, conversation_id, message_id, request_id),
            )
            cursor.execute(
                """
                UPDATE agent_conversation
                SET title = CASE WHEN NOT EXISTS (
                        SELECT 1 FROM agent_message WHERE conversation_id = %s AND role = 'USER'
                        AND id <> %s
                    ) THEN %s ELSE title END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (conversation_id, message_id, content[:120], conversation_id),
            )
        return message_id, task_id

    def turn_context(self, user_id: UUID, conversation_id: UUID) -> list[dict[str, str]]:
        self._assert_owned(user_id, conversation_id)
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT role, content FROM agent_message
                WHERE conversation_id = %s ORDER BY sequence_number DESC LIMIT 16
                """,
                (conversation_id,),
            )
            rows = list(reversed(cursor.fetchall()))
            return [{"role": row["role"].lower(), "content": row["content"]} for row in rows]

    def task_for_regeneration(
        self, user_id: UUID, task_id: UUID
    ) -> tuple[UUID, str, list[dict[str, str]]]:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT task.conversation_id, message.content
                FROM agent_task task
                JOIN agent_conversation conversation ON conversation.id = task.conversation_id
                JOIN agent_message message ON message.id = task.user_message_id
                WHERE task.id = %s AND conversation.user_id = %s
                  AND conversation.status = 'ACTIVE'
                """,
                (task_id, user_id),
            )
            row = cursor.fetchone()
            if row is None:
                raise AgentRecordNotFound("TASK_NOT_FOUND")
            cursor.execute(
                """
                UPDATE agent_task SET status = 'RUNNING', error_code = NULL, completed_at = NULL
                WHERE id = %s
                """,
                (task_id,),
            )
        return (
            row["conversation_id"],
            row["content"],
            self.turn_context(user_id, row["conversation_id"]),
        )

    def finish_turn(
        self,
        user_id: UUID,
        conversation_id: UUID,
        task_id: UUID,
        result: WorkflowResult,
        request_id: str,
    ) -> PersistedTurn:
        message_id, result_id = uuid4(), uuid4()
        with self._connection() as connection, connection.cursor() as cursor:
            self._lock_owned_conversation(cursor, user_id, conversation_id)
            sequence = self._next_sequence(cursor, conversation_id)
            cursor.execute(
                """
                INSERT INTO agent_message(id, conversation_id, role, content, sequence_number)
                VALUES (%s, %s, 'ASSISTANT', %s, %s)
                """,
                (message_id, conversation_id, result.content, sequence),
            )
            cursor.execute(
                """
                SELECT COALESCE(MAX(version_number), 0) + 1 AS version
                FROM agent_result_version WHERE task_id = %s
                """,
                (task_id,),
            )
            version = cursor.fetchone()["version"]
            cursor.execute(
                """
                INSERT INTO agent_result_version(
                    id, task_id, assistant_message_id, version_number, content,
                    structured_result, basis, limitations, model_name, fallback_used)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s)
                """,
                (
                    result_id,
                    task_id,
                    message_id,
                    version,
                    result.content,
                    self._json(result.structured_result),
                    self._json(result.basis),
                    self._json(result.limitations),
                    result.model_name,
                    result.fallback_used,
                ),
            )
            cursor.execute(
                """
                UPDATE agent_task
                SET intent = %s, status = %s, missing_fields = %s::jsonb,
                    error_code = %s, completed_at = CURRENT_TIMESTAMP
                WHERE id = %s AND conversation_id = %s
                """,
                (
                    result.intent.value,
                    result.status.value,
                    self._json(result.missing_fields),
                    "MODEL_UNAVAILABLE" if result.fallback_used else None,
                    task_id,
                    conversation_id,
                ),
            )
            cursor.execute(
                """
                UPDATE agent_conversation
                SET current_intent = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s
                """,
                (result.intent.value, conversation_id),
            )
            for call in result.tool_calls:
                self._insert_tool_call(cursor, task_id, call, request_id)
        return PersistedTurn(
            taskId=task_id, messageId=message_id, resultVersionId=result_id, result=result
        )

    def save_feedback(
        self, identity: IdentityContext, result_id: UUID, feedback: FeedbackCreate
    ) -> None:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO agent_feedback(id, result_version_id, user_id, category, comment)
                SELECT %s, result.id, %s, %s, %s
                FROM agent_result_version result
                JOIN agent_task task ON task.id = result.task_id
                JOIN agent_conversation conversation ON conversation.id = task.conversation_id
                WHERE result.id = %s AND conversation.user_id = %s
                ON CONFLICT (result_version_id, user_id)
                DO UPDATE SET category = EXCLUDED.category, comment = EXCLUDED.comment,
                              created_at = CURRENT_TIMESTAMP
                """,
                (
                    uuid4(),
                    identity.user_id,
                    feedback.category.value,
                    feedback.comment,
                    result_id,
                    identity.user_id,
                ),
            )
            if cursor.rowcount != 1:
                raise AgentRecordNotFound("RESULT_NOT_FOUND")

    def save_memory(self, identity: IdentityContext, scope: str, summary: str) -> UUID:
        if not identity.authorizations.get(scope, False):
            raise PermissionError("DATA_SCOPE_DENIED")
        memory_id = uuid4()
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO user_long_term_memory(id, user_id, data_scope, content_summary)
                VALUES (%s, %s, %s, %s)
                """,
                (memory_id, identity.user_id, scope, summary),
            )
        return memory_id

    def list_memories(self, user_id: UUID) -> list[dict[str, Any]]:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, data_scope AS "dataScope", content_summary AS "contentSummary",
                       created_at AS "createdAt"
                FROM user_long_term_memory
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (user_id,),
            )
            return list(cursor.fetchall())

    def update_memory(self, user_id: UUID, memory_id: UUID, summary: str) -> None:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE user_long_term_memory SET content_summary = %s
                WHERE id = %s AND user_id = %s
                """,
                (summary, memory_id, user_id),
            )
            if cursor.rowcount != 1:
                raise AgentRecordNotFound("MEMORY_NOT_FOUND")

    def delete_memory(self, user_id: UUID, memory_id: UUID) -> None:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM user_long_term_memory WHERE id = %s AND user_id = %s",
                (memory_id, user_id),
            )
            if cursor.rowcount != 1:
                raise AgentRecordNotFound("MEMORY_NOT_FOUND")

    def _assert_owned(self, user_id: UUID, conversation_id: UUID) -> None:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1 FROM agent_conversation
                WHERE id = %s AND user_id = %s AND status = 'ACTIVE'
                """,
                (conversation_id, user_id),
            )
            if cursor.fetchone() is None:
                raise AgentRecordNotFound("CONVERSATION_NOT_FOUND")

    def _lock_owned_conversation(
        self, cursor: psycopg.Cursor[dict[str, Any]], user_id: UUID, conversation_id: UUID
    ) -> None:
        cursor.execute(
            """
            SELECT 1 FROM agent_conversation
            WHERE id = %s AND user_id = %s AND status = 'ACTIVE' FOR UPDATE
            """,
            (conversation_id, user_id),
        )
        if cursor.fetchone() is None:
            raise AgentRecordNotFound("CONVERSATION_NOT_FOUND")

    def _next_sequence(self, cursor: psycopg.Cursor[dict[str, Any]], conversation_id: UUID) -> int:
        cursor.execute(
            """
            SELECT COALESCE(MAX(sequence_number), 0) + 1 AS value
            FROM agent_message WHERE conversation_id = %s
            """,
            (conversation_id,),
        )
        return int(cursor.fetchone()["value"])

    def _insert_tool_call(
        self,
        cursor: psycopg.Cursor[dict[str, Any]],
        task_id: UUID,
        call: ToolCallTrace,
        request_id: str,
    ) -> None:
        cursor.execute(
            """
            INSERT INTO agent_tool_call(
                id, task_id, tool_name, tool_version, arguments, result, status,
                error_type, duration_ms, request_id, completed_at)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (
                uuid4(),
                task_id,
                call.tool_name,
                call.tool_version,
                self._json(call.arguments),
                self._json(call.result) if call.result is not None else None,
                call.status,
                call.error_type,
                call.duration_ms,
                request_id,
            ),
        )

    def _summary(self, row: dict[str, Any]) -> ConversationSummary:
        return ConversationSummary(
            id=row["id"],
            title=row["title"],
            currentIntent=Intent(row["current_intent"]) if row["current_intent"] else None,
            updatedAt=row["updated_at"],
        )

    def _message(self, row: dict[str, Any]) -> MessageView:
        return MessageView(
            id=row["id"],
            role=row["role"],
            content=row["content"],
            sequenceNumber=row["sequence_number"],
            resultVersionId=row["result_version_id"],
            taskId=row["task_id"],
            intent=Intent(row["intent"]) if row["intent"] else None,
            fallbackUsed=row["fallback_used"],
            basis=row["basis"],
            limitations=row["limitations"],
            createdAt=row["created_at"],
        )

    def _json(self, value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, default=str)
