"""Grounded library-first recommendations with a bounded Open Library fallback."""

import json
import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote_plus

import httpx

from agent_service.agent_models import (
    LibraryBookCandidate,
    LibraryRecommendationItem,
    LibraryRecommendationRequest,
)
from agent_service.llm import ModelUnavailable, OpenAICompatibleModel

_HIGH_MATCH_SCORE = 85
_MIN_MATCH_SCORE = 55
_RESULT_LIMIT = 6


async def recommend_books(
    payload: LibraryRecommendationRequest, model: OpenAICompatibleModel
) -> list[LibraryRecommendationItem]:
    """Rank real holdings first and consult Open Library only without a high match."""

    first = await model.complete_json(
        _catalog_system_prompt(),
        json.dumps(
            {
                "requirement": payload.requirement,
                "libraryBooks": [
                    book.model_dump(mode="json", by_alias=True) for book in payload.books
                ],
            },
            ensure_ascii=False,
        ),
    )
    internal = _validated_internal(first, payload.books)
    if internal and internal[0].score >= _HIGH_MATCH_SCORE:
        return internal[:_RESULT_LIMIT]

    query = str(first.get("externalQuery") or payload.requirement).strip()[:160]
    external = await _search_open_library(query)
    if len(external) < _RESULT_LIMIT:
        try:
            query_result = await model.complete_json(
                (
                    "把用户的中文或英文选书需求转换为适合 Open Library 搜索的3至6个英文关键词。"
                    "同时给出最多6个可能符合需求的真实英文书名加作者，用于书目数据库二次核验。"
                    "不要解释、标点或site语法。只返回JSON："
                    '{"query":"keywords","titleQueries":["book title author"]}。'
                ),
                payload.requirement,
            )
            retry_query = str(query_result.get("query") or "").strip()[:120]
            raw_titles = query_result.get("titleQueries") or query_result.get("title_queries")
            title_queries = raw_titles if isinstance(raw_titles, list) else []
            search_queries = [retry_query, *title_queries[:6]]
            seen_keys = {candidate["key"] for candidate in external}
            seen_titles = {
                re.sub(r"[^\w]+", "", candidate["name"].casefold()) for candidate in external
            }
            for search_query in search_queries:
                if not isinstance(search_query, str) or not search_query.strip():
                    continue
                if search_query.strip().lower() == query.lower():
                    continue
                for candidate in await _search_open_library(search_query.strip()[:120]):
                    normalized_title = re.sub(r"[^\w]+", "", candidate["name"].casefold())
                    if candidate["key"] in seen_keys or normalized_title in seen_titles:
                        continue
                    external.append(candidate)
                    seen_keys.add(candidate["key"])
                    seen_titles.add(normalized_title)
                if len(external) >= 18:
                    break
            external = external[:18]
        except ModelUnavailable:
            pass
    if not external:
        return internal[:_RESULT_LIMIT]

    try:
        second = await model.complete_json(
            _mixed_system_prompt(),
            json.dumps(
                {
                    "requirement": payload.requirement,
                    "libraryCandidates": [_item_for_model(item) for item in internal[:12]],
                    "externalCandidates": external,
                },
                ensure_ascii=False,
            ),
        )
    except ModelUnavailable:
        return internal[:_RESULT_LIMIT]
    mixed = _validated_mixed(second, internal, external)
    if not mixed:
        return _fallback_external(external)[:_RESULT_LIMIT]

    seen = {item.key for item in mixed}
    remaining = [candidate for candidate in external if candidate["key"] not in seen]
    completed = mixed + _fallback_external(remaining)
    return sorted(
        completed,
        key=lambda item: (-item.score, item.source_type != "LIBRARY", item.name),
    )[:_RESULT_LIMIT]


def _catalog_system_prompt() -> str:
    return (
        "你是智慧图书馆选书助手。只评估libraryBooks中的真实馆藏，不得编造书籍或id。"
        "根据用户原始需求与书名、作者、类别、标签、简介、语言综合判断内容适配度，库存只用于"
        "同等适配度排序，不得让库存掩盖内容不匹配。score为0至100；85分以上只用于真正高度"
        "匹配的书。reason用一到两句话，必须引用该书真实特征并对应用户需求，不得声称未知事实。"
        "同时生成适合Open Library检索的简短externalQuery，必要时把中文主题转换为常见英文书目"
        '关键词。返回JSON：{"recommendations":[{"bookId":"uuid","score":整数,'
        '"reason":"理由"}],"externalQuery":"关键词"}。按score降序，最多12项。'
    )


def _mixed_system_prompt() -> str:
    return (
        "你是智慧图书馆选书助手。馆内没有高度匹配结果，现在对给定的馆内与Open Library馆外候选"
        "统一评估。只能返回候选中的key，不得补充任何候选外书籍。内容适配度优先；相近时馆内"
        "LIBRARY优先。reason必须结合候选现有字段说明与用户需求的关系，不能编造内容。score为"
        '0至100。返回JSON：{"recommendations":[{"key":"候选key","score":整数,'
        '"reason":"理由"}]}，按score降序；候选不少于6项时必须返回6项，否则全部返回。'
    )


def _validated_internal(
    raw: dict[str, Any], books: list[LibraryBookCandidate]
) -> list[LibraryRecommendationItem]:
    available = {str(book.id): book for book in books}
    result: list[LibraryRecommendationItem] = []
    seen: set[str] = set()
    for value in raw.get("recommendations", [])[:20]:
        if not isinstance(value, dict):
            continue
        book_id = str(value.get("bookId", ""))
        if book_id in seen or book_id not in available:
            continue
        score = _score(value.get("score"))
        if score < _MIN_MATCH_SCORE:
            continue
        book = available[book_id]
        result.append(_internal_item(book, score, _reason(value, book.name)))
        seen.add(book_id)
    return sorted(result, key=lambda item: (-item.score, not item.featured, item.name))


async def _search_open_library(query: str) -> list[dict[str, Any]]:
    fields = "key,title,author_name,first_publish_year,isbn,publisher,language,subject,cover_i"
    url = (
        "https://openlibrary.org/search.json?q="
        f"{quote_plus(query)}&fields={quote_plus(fields)}&limit=30&lang=zh"
    )
    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "School-Agent-Demo/1.0"})
            response.raise_for_status()
            docs = response.json().get("docs", [])
    except (httpx.HTTPError, ValueError, AttributeError):
        return []
    result: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    for doc in docs:
        if not isinstance(doc, dict) or not doc.get("key") or not doc.get("title"):
            continue
        normalized_title = re.sub(r"[^\w]+", "", str(doc["title"]).casefold())
        if not normalized_title or normalized_title in seen_titles:
            continue
        key = "EXT:" + str(doc["key"])
        cover_id = doc.get("cover_i")
        result.append(
            {
                "key": key,
                "name": str(doc["title"])[:200],
                "authors": _strings(doc.get("author_name"), 8),
                "publishedYear": _integer_or_none(doc.get("first_publish_year")),
                "isbn": next(iter(_strings(doc.get("isbn"), 1)), ""),
                "publisher": next(iter(_strings(doc.get("publisher"), 1)), ""),
                "language": ",".join(_strings(doc.get("language"), 3)),
                "tags": _strings(doc.get("subject"), 10),
                "coverImage": (
                    f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg?default=false"
                    if cover_id
                    else ""
                ),
                "externalUrl": "https://openlibrary.org" + str(doc["key"]),
            }
        )
        seen_titles.add(normalized_title)
        if len(result) >= 18:
            break
    return result


def _validated_mixed(
    raw: dict[str, Any],
    internal: list[LibraryRecommendationItem],
    external: list[dict[str, Any]],
) -> list[LibraryRecommendationItem]:
    choices: dict[str, tuple[str, Any]] = {item.key: ("LIBRARY", item) for item in internal}
    choices.update({item["key"]: ("EXTERNAL", item) for item in external})
    result: list[LibraryRecommendationItem] = []
    seen: set[str] = set()
    queried_at = datetime.now(UTC)
    for value in raw.get("recommendations", [])[:12]:
        if not isinstance(value, dict):
            continue
        key = str(value.get("key", ""))
        if key not in choices and key.startswith("/works/"):
            key = "EXT:" + key
        if key not in choices and not key.startswith("LIB:"):
            library_key = "LIB:" + key
            if library_key in choices:
                key = library_key
        if key in seen or key not in choices:
            continue
        score = _score(value.get("score"))
        if score < _MIN_MATCH_SCORE:
            continue
        source, candidate = choices[key]
        reason = _reason(value, candidate.name if source == "LIBRARY" else candidate["name"])
        if source == "LIBRARY":
            base: LibraryRecommendationItem = candidate
            result.append(
                base.model_copy(
                    update={
                        "score": score,
                        "featured": score >= _HIGH_MATCH_SCORE,
                        "reason": reason,
                    }
                )
            )
        else:
            external_reason = (
                reason
                if reason.startswith("图书馆未找到")
                else f"图书馆未找到高度匹配馆藏；{reason}"
            )
            result.append(
                LibraryRecommendationItem(
                    key=key,
                    source_type="EXTERNAL",
                    score=score,
                    featured=score >= _HIGH_MATCH_SCORE,
                    reason=external_reason,
                    name=candidate["name"],
                    isbn=candidate["isbn"],
                    authors=candidate["authors"],
                    publisher=candidate["publisher"],
                    published_year=candidate["publishedYear"],
                    language=candidate["language"],
                    tags=candidate["tags"],
                    cover_image=candidate["coverImage"],
                    external_url=candidate["externalUrl"],
                    queried_at=queried_at,
                )
            )
        seen.add(key)
    # Content fit remains the primary ordering key; source only breaks exact ties.
    return sorted(
        result,
        key=lambda item: (-item.score, item.source_type != "LIBRARY", item.name),
    )


def _fallback_external(external: list[dict[str, Any]]) -> list[LibraryRecommendationItem]:
    """Keep a real-source fallback when the model returns unusable candidate keys."""

    queried_at = datetime.now(UTC)
    result = []
    for index, candidate in enumerate(external[:_RESULT_LIMIT]):
        tags = candidate["tags"][:3]
        basis = "、".join(tags) if tags else "书名与检索主题"
        result.append(
            LibraryRecommendationItem(
                key=candidate["key"],
                source_type="EXTERNAL",
                score=max(_MIN_MATCH_SCORE, 68 - index * 2),
                featured=False,
                reason=f"图书馆未找到高度匹配馆藏；该书在 Open Library 中的{basis}与需求接近。",
                name=candidate["name"],
                isbn=candidate["isbn"],
                authors=candidate["authors"],
                publisher=candidate["publisher"],
                published_year=candidate["publishedYear"],
                language=candidate["language"],
                tags=candidate["tags"],
                cover_image=candidate["coverImage"],
                external_url=candidate["externalUrl"],
                queried_at=queried_at,
            )
        )
    return result


def _internal_item(
    book: LibraryBookCandidate, score: int, reason: str
) -> LibraryRecommendationItem:
    return LibraryRecommendationItem(
        key="LIB:" + str(book.id),
        source_type="LIBRARY",
        score=score,
        featured=score >= _HIGH_MATCH_SCORE,
        reason=reason,
        book_id=book.id,
        name=book.name,
        isbn=book.isbn,
        authors=book.authors,
        publisher=book.publisher,
        published_year=book.published_year,
        language=book.language,
        category=book.category,
        tags=book.tags,
        summary=book.summary,
        cover_image=book.cover_image,
    )


def _item_for_model(item: LibraryRecommendationItem) -> dict[str, Any]:
    return {
        "key": item.key,
        "sourceType": "LIBRARY",
        "name": item.name,
        "authors": item.authors,
        "category": item.category,
        "tags": item.tags,
        "summary": item.summary,
        "scoreFromLibraryPass": item.score,
    }


def _score(value: Any) -> int:
    try:
        return min(100, max(0, int(value)))
    except (TypeError, ValueError):
        return 0


def _reason(value: dict[str, Any], name: str) -> str:
    reason = str(value.get("reason") or "").strip()
    return reason[:240] if reason else f"《{name}》与本次阅读主题较为接近。"


def _strings(value: Any, limit: int) -> list[str]:
    return [str(item)[:120] for item in value[:limit]] if isinstance(value, list) else []


def _integer_or_none(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
