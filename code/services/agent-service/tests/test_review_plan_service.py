from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest

from agent_service.review_plan_models import ReviewPlanCreateRequest
from agent_service.review_plan_service import ReviewPlanService, _plan_is_stale, allocate_minutes

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class FakeModel:
    model_name = "test-model"

    async def complete_json(self, system, user):
        del system
        import json

        payload = json.loads(user)
        return {
            "stageGuidance": [
                {
                    "key": stage["key"],
                    "objective": f"完成{stage['name']}",
                    "method": "教材回顾后完成限时练习",
                    "rationale": "日期与时长来自确定性计算",
                    # A model-supplied quota must be ignored.
                    "suggestedMinutes": 99999,
                }
                for stage in payload["fixedStages"]
            ],
            "priorityExplanation": "近期考试优先，同时纳入薄弱点证据。",
            "assumptions": ["每日按设定时长学习"],
            "limitations": ["不替代学校通知"],
        }


class FakeRepository:
    def __init__(self):
        self.generated = None

    def context(self, user_id, exam_ids, use_mastery):
        del user_id, use_mastery
        now = datetime.now(UTC)
        today = date.today()
        return {
            "exams": [
                {
                    "id": exam_ids[0],
                    "subject": "数据结构",
                    "exam_date": today + timedelta(days=5),
                    "start_time": "09:00",
                    "end_time": "11:00",
                    "location": "知行楼 101",
                    "updated_at": now,
                },
                {
                    "id": exam_ids[1],
                    "subject": "计算机网络",
                    "exam_date": today + timedelta(days=10),
                    "start_time": "14:00",
                    "end_time": "16:00",
                    "location": "知行楼 202",
                    "updated_at": now,
                },
            ],
            "mastery": [
                {
                    "course": "计算机网络",
                    "knowledge_point": "TCP 拥塞控制",
                    "mastery_score": 30,
                    "evidence_count": 3,
                    "correct_count": 1,
                }
            ],
            "mistakes": [
                {
                    "course": "计算机网络",
                    "knowledge_point": "TCP 拥塞控制",
                    "mistake_count": 3,
                    "causes": ["CONCEPT"],
                }
            ],
            "materials": [{"course": "数据结构", "relative_path": "chapter-1.pdf"}],
        }

    def save(self, user_id, generated, group_id, version, supersedes_id):
        del user_id, group_id, version, supersedes_id
        self.generated = generated
        return generated


def test_allocate_minutes_preserves_exact_budget() -> None:
    assert allocate_minutes(17, [1, 1, 1]) == [6, 6, 5]
    assert sum(allocate_minutes(121, [0.7, 0.2, 0.1])) == 121


async def test_plan_dates_and_minutes_are_not_controlled_by_model() -> None:
    repository = FakeRepository()
    exam_ids = [uuid4(), uuid4()]
    request = ReviewPlanCreateRequest(
        examIds=exam_ids,
        dailyMinutes=60,
        target="核心知识稳定达到 80 分",
        constraints="周三只能学习 30 分钟",
    )

    await ReviewPlanService(FakeModel(), repository).create(uuid4(), request, True)

    generated = repository.generated
    assert generated["totalMinutes"] == 600
    assert sum(stage["suggestedMinutes"] for stage in generated["stages"]) == 600
    assert all(stage["suggestedMinutes"] != 99999 for stage in generated["stages"])
    assert "TCP 拥塞控制" in {
        point for stage in generated["stages"] for point in stage["knowledgePoints"]
    }
    assert any("每日总时长" in item for item in generated["assumptions"])


def test_plan_becomes_stale_when_source_exam_is_edited_or_deleted() -> None:
    now = datetime.now(UTC)
    plan = {"input_snapshot": {"examIds": [str(uuid4()), str(uuid4())]}}
    unchanged = {"updated_at": now, "source_updated_at": now}

    assert _plan_is_stale(plan, [unchanged]) is True
    assert (
        _plan_is_stale(
            plan,
            [unchanged, {"updated_at": now + timedelta(seconds=1), "source_updated_at": now}],
        )
        is True
    )
    assert _plan_is_stale(plan, [unchanged, unchanged]) is False
