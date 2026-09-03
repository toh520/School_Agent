"""Application service that streams workflow progress and persists every terminal result."""

import asyncio
import json
import logging
import re
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi.concurrency import run_in_threadpool

from agent_service.agent_models import (
    IdentityContext,
    PersistedTurn,
    TaskStatus,
    WorkflowResult,
)
from agent_service.agent_repository import AgentRepository
from agent_service.knowledge_rag import (
    KnowledgeRagService,
    general_reference_prompt,
    grounded_prompt,
)
from agent_service.llm import ModelUnavailable, OpenAICompatibleModel
from agent_service.workflow import WorkflowEngine, follow_up_message, system_prompt

LOGGER = logging.getLogger(__name__)
NO_KNOWLEDGE_MESSAGE = "知识库未找到相关内容，暂时无法准确回答。"


def sse(event: str, data: object) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


class AgentOrchestrator:
    """Run one bounded Agent turn; all persistence occurs only through Agent-owned tables."""

    def __init__(
        self,
        repository: AgentRepository,
        workflow: WorkflowEngine,
        model: OpenAICompatibleModel,
        knowledge_rag: KnowledgeRagService,
    ) -> None:
        self._repository = repository
        self._workflow = workflow
        self._model = model
        self._knowledge_rag = knowledge_rag

    async def start(
        self,
        identity: IdentityContext,
        conversation_id: UUID,
        content: str,
        request_id: str,
    ) -> AsyncIterator[str]:
        _, task_id = await run_in_threadpool(
            self._repository.start_turn,
            identity.user_id,
            conversation_id,
            content,
            request_id,
        )
        history = await run_in_threadpool(
            self._repository.turn_context, identity.user_id, conversation_id
        )
        return self._stream(identity, conversation_id, task_id, content, history, request_id)

    async def regenerate(
        self, identity: IdentityContext, task_id: UUID, request_id: str
    ) -> AsyncIterator[str]:
        conversation_id, content, history = await run_in_threadpool(
            self._repository.task_for_regeneration, identity.user_id, task_id
        )
        return self._stream(identity, conversation_id, task_id, content, history, request_id)

    async def _stream(
        self,
        identity: IdentityContext,
        conversation_id: UUID,
        task_id: UUID,
        content: str,
        history: list[dict[str, str]],
        request_id: str,
    ) -> AsyncIterator[str]:
        yield sse("status", {"phase": "UNDERSTANDING", "label": "正在理解你的需求"})
        state = await self._workflow.prepare(content, history, identity)
        yield sse("intent", {"intent": state["intent"].value})

        if state["missing_fields"]:
            answer = follow_up_message(state["missing_fields"])
            yield sse(
                "status",
                {
                    "phase": "NEEDS_INPUT",
                    "label": "还需要少量信息",
                    "fields": state["missing_fields"],
                },
            )
            yield sse("content", {"delta": answer})
            result = WorkflowResult(
                intent=state["intent"],
                status=TaskStatus.NEEDS_INPUT,
                missingFields=state["missing_fields"],
                content=answer,
                structuredResult={"conditions": state["conditions"]},
                basis=["当前会话内容"],
                limitations=["信息补充前不会调用后续工具"],
            )
            persisted = await self._persist(identity, conversation_id, task_id, result, request_id)
            yield sse("done", persisted.model_dump(mode="json", by_alias=True))
            return

        yield sse("status", {"phase": "CHECKING", "label": "正在校验条件与权限"})
        for call in state["tool_calls"]:
            yield sse(
                "tool",
                {
                    "name": call.tool_name,
                    "status": call.status,
                    "durationMs": call.duration_ms,
                },
            )
        if any(call.status != "SUCCESS" for call in state["tool_calls"]):
            answer = "当前条件未通过工具校验，我没有继续生成结果。请检查数据授权或输入内容。"
            result = WorkflowResult(
                intent=state["intent"],
                status=TaskStatus.FAILED,
                content=answer,
                structuredResult={"conditions": state["conditions"]},
                basis=["受控工具校验"],
                limitations=["工具校验未通过"],
                toolCalls=state["tool_calls"],
            )
            yield sse("content", {"delta": answer})
            persisted = await self._persist(identity, conversation_id, task_id, result, request_id)
            yield sse("done", persisted.model_dump(mode="json", by_alias=True))
            return

        if state["intent"].value == "CAMPUS_QA":
            async for event in self._campus_answer(
                identity, conversation_id, task_id, content, history, state, request_id
            ):
                yield event
            return

        yield sse("status", {"phase": "RESPONDING", "label": "正在组织回答"})
        answer_parts: list[str] = []
        fallback = False
        try:
            model_history = [
                {
                    "role": item["role"] if item["role"] in ("user", "assistant") else "user",
                    "content": item["content"],
                }
                for item in history[-10:]
            ]
            answer = await self._model.complete(system_prompt(state), model_history)
            if not self._is_grounded_m04_answer(answer):
                raise ModelUnavailable("MODEL_UNGROUNDED")
            answer_parts.append(answer)
        except ModelUnavailable:
            fallback = True
        answer = "".join(answer_parts).strip()
        if not answer:
            fallback = True
            answer = self._fallback(state["intent"].value)
        for index in range(0, len(answer), 24):
            yield sse("content", {"delta": answer[index : index + 24]})
            await asyncio.sleep(0)
        limitations = ["对应领域的数据查询工具将在后续业务阶段接入"]
        if state.get("injection_detected"):
            limitations.append("已忽略改变系统规则或索取敏感信息的指令")
        if fallback:
            limitations.append("模型当前不可用，本次使用安全降级回答")
        result = WorkflowResult(
            intent=state["intent"],
            status=TaskStatus.DEGRADED if fallback else TaskStatus.COMPLETED,
            content=answer,
            structuredResult={"conditions": state["conditions"]},
            basis=["当前会话内容", "受控工具校验结果"],
            limitations=limitations,
            toolCalls=state["tool_calls"],
            modelName=None if fallback else self._model.model_name,
            fallbackUsed=fallback,
        )
        persisted = await self._persist(identity, conversation_id, task_id, result, request_id)
        yield sse("done", persisted.model_dump(mode="json", by_alias=True))

    async def _campus_answer(
        self,
        identity: IdentityContext,
        conversation_id: UUID,
        task_id: UUID,
        content: str,
        history: list[dict[str, str]],
        state: dict,
        request_id: str,
    ) -> AsyncIterator[str]:
        """Answer campus facts from RAG, with an explicit non-authoritative no-hit path."""

        yield sse("status", {"phase": "RETRIEVING", "label": "正在检索校内知识库"})
        recent_questions = [
            item["content"]
            for item in history[-5:]
            if item.get("role") == "user" and item.get("content")
        ]
        retrieval_query = "\n".join(recent_questions[-2:]) or content
        try:
            matches = await run_in_threadpool(self._knowledge_rag.search, retrieval_query)
        except Exception:
            # A model cache or database failure must not be disguised as a factual answer.
            LOGGER.exception("Campus knowledge retrieval failed")
            answer = "校园知识库暂时无法检索，因此当前无法准确回答。请稍后重试。"
            result = WorkflowResult(
                intent=state["intent"],
                status=TaskStatus.DEGRADED,
                content=answer,
                structuredResult={"knowledgeMatchCount": 0, "retrievalAvailable": False},
                basis=[],
                limitations=["校园知识库检索服务暂时不可用"],
                toolCalls=state["tool_calls"],
                fallbackUsed=True,
            )
            yield sse("content", {"delta": answer})
            persisted = await self._persist(identity, conversation_id, task_id, result, request_id)
            yield sse("done", persisted.model_dump(mode="json", by_alias=True))
            return

        model_history = [
            {
                "role": item["role"] if item["role"] in ("user", "assistant") else "user",
                "content": item["content"],
            }
            for item in history[-10:]
        ]
        if matches:
            yield sse("status", {"phase": "GROUNDING", "label": "正在核对相关资料"})
            fallback = False
            try:
                answer = (
                    await self._model.complete(grounded_prompt(matches), model_history)
                ).strip()
                if not answer:
                    raise ModelUnavailable("EMPTY_MODEL_RESPONSE")
            except ModelUnavailable:
                fallback = True
                answer = "已找到相关校内资料，但回答模型暂时不可用，请稍后重试。"
            result = WorkflowResult(
                intent=state["intent"],
                status=TaskStatus.DEGRADED if fallback else TaskStatus.COMPLETED,
                content=answer,
                structuredResult={
                    "knowledgeMatchCount": len(matches),
                    "knowledgeDocumentIds": list(
                        dict.fromkeys(str(item.document_id) for item in matches)
                    ),
                },
                basis=[],
                limitations=["回答仅依据当前有效的校内知识库"]
                if not fallback
                else ["回答模型暂时不可用"],
                toolCalls=state["tool_calls"],
                modelName=None if fallback else self._model.model_name,
                fallbackUsed=fallback,
            )
        else:
            fallback = True
            try:
                general = (
                    await self._model.complete(general_reference_prompt(), model_history)
                ).strip()
            except ModelUnavailable:
                general = ""
            answer = NO_KNOWLEDGE_MESSAGE
            if general:
                answer += f"\n\n一般性参考（非校内知识库依据）：{general}"
            result = WorkflowResult(
                intent=state["intent"],
                status=TaskStatus.DEGRADED,
                content=answer,
                structuredResult={"knowledgeMatchCount": 0, "retrievalAvailable": True},
                basis=[],
                limitations=["一般性参考不代表本校规定，请向学校对应部门核实"],
                toolCalls=state["tool_calls"],
                modelName=self._model.model_name if general else None,
                fallbackUsed=fallback,
            )

        yield sse("status", {"phase": "RESPONDING", "label": "正在组织回答"})
        for index in range(0, len(result.content), 24):
            yield sse("content", {"delta": result.content[index : index + 24]})
            await asyncio.sleep(0)
        persisted = await self._persist(identity, conversation_id, task_id, result, request_id)
        yield sse("done", persisted.model_dump(mode="json", by_alias=True))

    async def _persist(
        self,
        identity: IdentityContext,
        conversation_id: UUID,
        task_id: UUID,
        result: WorkflowResult,
        request_id: str,
    ) -> PersistedTurn:
        return await run_in_threadpool(
            self._repository.finish_turn,
            identity.user_id,
            conversation_id,
            task_id,
            result,
            request_id,
        )

    def _fallback(self, intent: str) -> str:
        names = {
            "FOOD": "智能食堂",
            "EXAM": "考试与学习规划",
            "BOOK": "图书与馆藏推荐",
            "CAMPUS_QA": "校园知识问答",
            "UNKNOWN": "校园事务",
        }
        return (
            f"我已识别这是“{names[intent]}”方向的请求，并保留了本轮条件。"
            "对应领域工具接入后才能给出有数据依据的结果，当前不会提供未经核实的校园事实。"
        )

    @staticmethod
    def _is_grounded_m04_answer(answer: str) -> bool:
        """Reject answer shapes that tend to smuggle in ungrounded domain claims."""

        if not answer or len(answer) > 220:
            return False
        list_pattern = r"(^|\n)\s*(?:[-*•]|\d+[.、)]|[一二三四五六七八九十]+[、.)])"
        forbidden_claims = ("材料包括", "需要准备", "办理步骤", "申请条件", "具体地点")
        return not re.search(list_pattern, answer) and not any(
            claim in answer for claim in forbidden_claims
        )
