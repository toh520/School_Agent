"""Deterministic exam planning with model-authored, quota-bound learning guidance."""

import asyncio
import json
import math
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import psycopg
from psycopg.rows import dict_row

from agent_service.config import Settings
from agent_service.llm import OpenAICompatibleModel
from agent_service.review_plan_models import ReviewPlanCreateRequest, ReviewPlanView

PHASES = (
    ("FOUNDATION", "基础回顾", 0.55),
    ("PRACTICE", "强化训练", 0.30),
    ("SPRINT", "考前冲刺", 0.15),
)


def allocate_minutes(total: int, weights: list[float]) -> list[int]:
    """Use largest remainders so every generated plan preserves the exact time budget."""

    if total < 0 or not weights or sum(weights) <= 0:
        raise ValueError("复习时间参数无效")
    raw = [total * weight / sum(weights) for weight in weights]
    result = [math.floor(value) for value in raw]
    for index in sorted(range(len(raw)), key=lambda item: raw[item] - result[item], reverse=True)[
        : total - sum(result)
    ]:
        result[index] += 1
    return result


class ReviewPlanRepository:
    """Store plan snapshots and versions while enforcing ownership in every query."""

    def __init__(self, settings: Settings) -> None:
        self._connect = {
            "host": settings.db_host,
            "port": settings.db_port,
            "dbname": settings.db_name,
            "user": settings.db_username,
            "password": settings.db_password.get_secret_value(),
            "connect_timeout": 5,
        }

    def context(self, user_id: UUID, exam_ids: list[UUID], use_mastery: bool) -> dict[str, Any]:
        """Load authoritative exams and optional authorized weakness evidence."""

        with (
            psycopg.connect(**self._connect, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """
                SELECT id, subject, exam_date, start_time, end_time, location, updated_at
                FROM exam_record
                WHERE user_id = %s AND id = ANY(%s) AND exam_date >= CURRENT_DATE
                ORDER BY exam_date, start_time
                """,
                (user_id, exam_ids),
            )
            exams = [dict(row) for row in cursor.fetchall()]
            if len(exams) != len(exam_ids):
                raise ValueError("部分考试不存在、已过期或不属于当前用户")
            subjects = [str(item["subject"]) for item in exams]
            mastery: list[dict[str, Any]] = []
            mistakes: list[dict[str, Any]] = []
            if use_mastery:
                cursor.execute(
                    """
                    SELECT course, knowledge_point, mastery_score, evidence_count, correct_count
                    FROM knowledge_mastery
                    WHERE user_id = %s AND course = ANY(%s)
                    ORDER BY mastery_score, evidence_count DESC
                    """,
                    (user_id, subjects),
                )
                mastery = [dict(row) for row in cursor.fetchall()]
                cursor.execute(
                    """
                    SELECT course, knowledge_point, count(*) AS mistake_count,
                           array_agg(DISTINCT cause_type) AS causes
                    FROM mistake_record
                    WHERE user_id = %s AND course = ANY(%s) AND mastered = FALSE
                    GROUP BY course, knowledge_point
                    ORDER BY count(*) DESC
                    """,
                    (user_id, subjects),
                )
                mistakes = [dict(row) for row in cursor.fetchall()]
            cursor.execute(
                """
                SELECT course, relative_path
                FROM study_material
                WHERE active = TRUE AND parse_status = 'INDEXED' AND course = ANY(%s)
                ORDER BY course, relative_path LIMIT 80
                """,
                (subjects,),
            )
            materials = [dict(row) for row in cursor.fetchall()]
        return {"exams": exams, "mastery": mastery, "mistakes": mistakes, "materials": materials}

    def save(
        self,
        user_id: UUID,
        generated: dict[str, Any],
        group_id: UUID,
        version: int,
        supersedes_id: UUID | None,
    ) -> ReviewPlanView:
        """Persist one immutable version and atomically move the current-version pointer."""

        plan_id = uuid4()
        with psycopg.connect(**self._connect) as connection, connection.cursor() as cursor:
            cursor.execute(
                "UPDATE review_plan SET is_current = FALSE, status = 'ARCHIVED', "
                "updated_at = CURRENT_TIMESTAMP WHERE user_id = %s AND plan_group_id = %s",
                (user_id, group_id),
            )
            cursor.execute(
                """
                INSERT INTO review_plan(
                    id, user_id, plan_group_id, version_number, is_current, title, status,
                    input_snapshot, priority_explanation, assumptions, limitations,
                    total_minutes, model_name, data_as_of, target, constraints_text, supersedes_id)
                VALUES (%s, %s, %s, %s, TRUE, %s, 'ACTIVE', %s::jsonb, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s)
                """,
                (
                    plan_id,
                    user_id,
                    group_id,
                    version,
                    generated["title"],
                    json.dumps(generated["snapshot"], ensure_ascii=False, default=str),
                    generated["priorityExplanation"],
                    generated["assumptions"],
                    generated["limitations"],
                    generated["totalMinutes"],
                    generated["modelName"],
                    generated["dataAsOf"],
                    generated["target"],
                    generated["constraints"],
                    supersedes_id,
                ),
            )
            for exam in generated["exams"]:
                cursor.execute(
                    """
                    INSERT INTO review_plan_exam(
                        plan_id, exam_id, priority_score, source_updated_at, allocated_minutes)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        plan_id,
                        exam["id"],
                        exam["priorityScore"],
                        exam["updatedAt"],
                        exam["allocatedMinutes"],
                    ),
                )
            for index, stage in enumerate(generated["stages"]):
                cursor.execute(
                    """
                    INSERT INTO review_plan_stage(
                        plan_id, stage_index, name, phase, start_date, end_date, subject,
                        knowledge_points, objective, suggested_minutes, method, rationale)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        plan_id,
                        index,
                        stage["name"],
                        stage["phase"],
                        stage["startDate"],
                        stage["endDate"],
                        stage["subject"],
                        stage["knowledgePoints"],
                        stage["objective"],
                        stage["suggestedMinutes"],
                        stage["method"],
                        stage["rationale"],
                    ),
                )
            cursor.execute(
                """
                INSERT INTO learning_activity(
                    user_id, activity_type, course, summary, related_entity_id)
                VALUES (%s, 'PLAN', %s, %s, %s)
                """,
                (user_id, generated["title"], f"生成复习计划 v{version}", plan_id),
            )
        return self.get(user_id, plan_id)

    def get(self, user_id: UUID, plan_id: UUID) -> ReviewPlanView:
        with (
            psycopg.connect(**self._connect, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                "SELECT * FROM review_plan WHERE user_id = %s AND id = %s", (user_id, plan_id)
            )
            plan = cursor.fetchone()
            if not plan:
                raise ValueError("复习计划不存在")
            cursor.execute(
                """
                SELECT e.id, e.subject, e.exam_date, e.start_time, e.location, e.updated_at,
                       pe.priority_score, pe.source_updated_at,
                       pe.allocated_minutes
                FROM review_plan_exam pe JOIN exam_record e ON e.id = pe.exam_id
                WHERE pe.plan_id = %s
                ORDER BY e.exam_date, e.start_time
                """,
                (plan_id,),
            )
            exams = [dict(row) for row in cursor.fetchall()]
            cursor.execute(
                "SELECT * FROM review_plan_stage WHERE plan_id = %s ORDER BY stage_index",
                (plan_id,),
            )
            stages = [dict(row) for row in cursor.fetchall()]
        stale = _plan_is_stale(plan, exams)
        for exam in exams:
            exam["start_time"] = str(exam["start_time"])[:5]
        return ReviewPlanView(
            **dict(plan),
            constraints=plan["constraints_text"],
            stale=stale,
            exams=exams,
            stages=stages,
        )

    def list(self, user_id: UUID) -> list[ReviewPlanView]:
        with (
            psycopg.connect(**self._connect, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                "SELECT id FROM review_plan WHERE user_id = %s ORDER BY created_at DESC LIMIT 30",
                (user_id,),
            )
            ids = [row["id"] for row in cursor.fetchall()]
        return [self.get(user_id, plan_id) for plan_id in ids]

    def latest_version(self, user_id: UUID, plan_id: UUID) -> tuple[UUID, int]:
        with (
            psycopg.connect(**self._connect, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                "SELECT plan_group_id, max(version_number) AS version FROM review_plan "
                "WHERE user_id = %s AND plan_group_id = "
                "(SELECT plan_group_id FROM review_plan WHERE user_id = %s AND id = %s) "
                "GROUP BY plan_group_id",
                (user_id, user_id, plan_id),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("复习计划不存在")
            return row["plan_group_id"], int(row["version"])

    def delete_group(self, user_id: UUID, plan_id: UUID) -> None:
        with psycopg.connect(**self._connect) as connection, connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM review_plan WHERE user_id = %s AND plan_group_id = "
                "(SELECT plan_group_id FROM review_plan WHERE user_id = %s AND id = %s)",
                (user_id, user_id, plan_id),
            )
            if cursor.rowcount == 0:
                raise ValueError("复习计划不存在")


class ReviewPlanService:
    """Compute factual dates and quotas locally; use the model only for study guidance."""

    def __init__(
        self,
        model: OpenAICompatibleModel,
        repository: ReviewPlanRepository,
        timezone_name: str = "Asia/Shanghai",
    ) -> None:
        self._model = model
        self._repository = repository
        self._timezone = ZoneInfo(timezone_name)

    async def create(
        self,
        user_id: UUID,
        request: ReviewPlanCreateRequest,
        use_mastery: bool,
        group_id: UUID | None = None,
        version: int = 1,
        supersedes_id: UUID | None = None,
    ) -> ReviewPlanView:
        context = await asyncio.to_thread(
            self._repository.context, user_id, request.exam_ids, use_mastery
        )
        generated = await self._generate(request, context)
        return await asyncio.to_thread(
            self._repository.save,
            user_id,
            generated,
            group_id or uuid4(),
            version,
            supersedes_id,
        )

    async def regenerate(self, user_id: UUID, plan_id: UUID, use_mastery: bool) -> ReviewPlanView:
        previous = await asyncio.to_thread(self._repository.get, user_id, plan_id)
        group_id, version = await asyncio.to_thread(
            self._repository.latest_version, user_id, plan_id
        )
        snapshot = previous.input_snapshot
        request = ReviewPlanCreateRequest(
            examIds=snapshot["examIds"],
            dailyMinutes=snapshot["dailyMinutes"],
            target=previous.target,
            constraints=previous.constraints,
        )
        return await self.create(user_id, request, use_mastery, group_id, version + 1, plan_id)

    async def list(self, user_id: UUID) -> list[ReviewPlanView]:
        return await asyncio.to_thread(self._repository.list, user_id)

    async def get(self, user_id: UUID, plan_id: UUID) -> ReviewPlanView:
        return await asyncio.to_thread(self._repository.get, user_id, plan_id)

    async def delete(self, user_id: UUID, plan_id: UUID) -> None:
        await asyncio.to_thread(self._repository.delete_group, user_id, plan_id)

    async def _generate(
        self, request: ReviewPlanCreateRequest, context: dict[str, Any]
    ) -> dict[str, Any]:
        today = datetime.now(self._timezone).date()
        exams = context["exams"]
        farthest_days = max(1, max((exam["exam_date"] - today).days for exam in exams))
        total_minutes = request.daily_minutes * farthest_days
        weakness = _weakness_by_subject(context)
        weights = [
            (1 + weakness.get(exam["subject"], {}).get("factor", 0))
            / math.sqrt(max(1, (exam["exam_date"] - today).days))
            for exam in exams
        ]
        subject_minutes = allocate_minutes(total_minutes, weights)
        fixed_stages = _fixed_stages(exams, subject_minutes, weakness, today)
        prompt_context = {
            "target": request.target,
            "constraints": request.constraints,
            "exams": [
                _json_safe_exam(exam, minutes, weights[index])
                for index, (exam, minutes) in enumerate(zip(exams, subject_minutes, strict=True))
            ],
            "fixedStages": fixed_stages,
            "weakPoints": context["mistakes"],
            "mastery": context["mastery"],
            "materials": context["materials"],
        }
        model_output = await self._model.complete_json(
            _plan_system(), json.dumps(prompt_context, ensure_ascii=False, default=str)
        )
        guidance = _validated_guidance(model_output, fixed_stages)
        data_as_of = datetime.now(UTC)
        stages = [{**stage, **guidance[stage["key"]]} for stage in fixed_stages]
        assumptions = _strings(model_output.get("assumptions"), ["每日可按设定时长完成复习"])
        if request.constraints:
            assumptions.append("补充偏好仅调整学习方法，每日总时长仍按用户设定值核算")
        return {
            "title": f"{exams[0]['subject']}{'等科目' if len(exams) > 1 else ''}复习计划",
            "target": request.target,
            "constraints": request.constraints,
            "snapshot": {
                "examIds": [str(exam["id"]) for exam in exams],
                "dailyMinutes": request.daily_minutes,
                "target": request.target,
                "constraints": request.constraints,
                "weakPoints": context["mistakes"],
                "mastery": context["mastery"],
                "materialCount": len(context["materials"]),
            },
            "priorityExplanation": str(
                model_output.get("priorityExplanation")
                or "按考试迫近程度和已授权的薄弱点分配复习时间。"
            )[:2000],
            "assumptions": assumptions,
            "limitations": _strings(
                model_output.get("limitations"), ["计划不代替学校发布的正式考试通知"]
            ),
            "totalMinutes": total_minutes,
            "modelName": self._model.model_name,
            "dataAsOf": data_as_of,
            "exams": [
                _json_safe_exam(exam, subject_minutes[index], weights[index])
                for index, exam in enumerate(exams)
            ],
            "stages": stages,
        }


def _weakness_by_subject(context: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in context["mastery"]:
        target = result.setdefault(item["course"], {"points": [], "factor": 0.0})
        target["points"].append(item["knowledge_point"])
        target["factor"] += max(0.0, (70 - float(item["mastery_score"])) / 100)
    for item in context["mistakes"]:
        target = result.setdefault(item["course"], {"points": [], "factor": 0.0})
        target["points"].append(item["knowledge_point"])
        target["factor"] += min(0.5, int(item["mistake_count"]) * 0.1)
    return result


def _plan_is_stale(plan: dict[str, Any], exams: list[dict[str, Any]]) -> bool:
    """Treat edited or deleted source exams as a stale immutable plan snapshot."""

    snapshot = plan.get("input_snapshot")
    expected = snapshot.get("examIds", []) if isinstance(snapshot, dict) else []
    return len(exams) != len(expected) or any(
        exam["updated_at"] > exam["source_updated_at"] for exam in exams
    )


def _fixed_stages(
    exams: list[dict[str, Any]],
    allocations: list[int],
    weakness: dict[str, dict[str, Any]],
    today: date,
) -> list[dict[str, Any]]:
    stages: list[dict[str, Any]] = []
    for exam, total in zip(exams, allocations, strict=True):
        phase_minutes = allocate_minutes(total, [phase[2] for phase in PHASES])
        days = max(1, (exam["exam_date"] - today).days)
        boundaries = [
            (today, max(today, exam["exam_date"] - timedelta(days=max(2, math.ceil(days * 0.35))))),
            (
                max(today, exam["exam_date"] - timedelta(days=max(1, math.ceil(days * 0.35) - 1))),
                max(today, exam["exam_date"] - timedelta(days=1)),
            ),
            (max(today, exam["exam_date"] - timedelta(days=1)), exam["exam_date"]),
        ]
        for (phase, label, _), minutes, boundary in zip(
            PHASES, phase_minutes, boundaries, strict=True
        ):
            stages.append(
                {
                    "key": f"{exam['id']}:{phase}",
                    "name": f"{exam['subject']} · {label}",
                    "phase": phase,
                    "startDate": boundary[0],
                    "endDate": boundary[1],
                    "subject": exam["subject"],
                    "knowledgePoints": list(
                        dict.fromkeys(weakness.get(exam["subject"], {}).get("points", []))
                    )[:8],
                    "suggestedMinutes": minutes,
                }
            )
    return stages


def _json_safe_exam(exam: dict[str, Any], minutes: int, score: float) -> dict[str, Any]:
    return {
        "id": exam["id"],
        "subject": exam["subject"],
        "examDate": exam["exam_date"],
        "startTime": str(exam["start_time"])[:5],
        "location": exam["location"],
        "updatedAt": exam["updated_at"],
        "priorityScore": round(score, 3),
        "allocatedMinutes": minutes,
    }


def _validated_guidance(
    raw: dict[str, Any], stages: list[dict[str, Any]]
) -> dict[str, dict[str, str]]:
    items = raw.get("stageGuidance")
    if not isinstance(items, list):
        raise ValueError("大模型未返回完整的复习阶段建议")
    by_key = {str(item.get("key")): item for item in items if isinstance(item, dict)}
    if set(by_key) != {stage["key"] for stage in stages}:
        raise ValueError("大模型返回的复习阶段不完整")
    result = {
        key: {
            "objective": str(item.get("objective") or "").strip()[:1000],
            "method": str(item.get("method") or "").strip()[:1000],
            "rationale": str(item.get("rationale") or "").strip()[:1000],
        }
        for key, item in by_key.items()
    }
    if any(not all(guidance.values()) for guidance in result.values()):
        raise ValueError("大模型返回的复习阶段建议缺少必要内容")
    return result


def _strings(value: Any, fallback: list[str]) -> list[str]:
    if not isinstance(value, list):
        return fallback
    result = [str(item).strip()[:500] for item in value if str(item).strip()]
    return result[:8] or fallback


def _plan_system() -> str:
    return """
你是大学复习计划助手。输入中的考试日期、阶段日期和分钟数由程序核算，不得修改。
只为每个 fixedStages.key 补充 objective、method、rationale。
薄弱点有证据时说明优先原因，无证据时明确说明。
返回 JSON：{"stageGuidance":[{"key":"...","objective":"...","method":"...","rationale":"..."}],
"priorityExplanation":"...","assumptions":["..."],"limitations":["..."]}。不得输出输入中没有的考试事实。
""".strip()
