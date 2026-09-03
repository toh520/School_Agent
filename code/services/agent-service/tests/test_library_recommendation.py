import asyncio
from uuid import uuid4

from agent_service.agent_models import LibraryBookCandidate, LibraryRecommendationRequest
from agent_service.library_recommendation import recommend_books


class StubModel:
    def __init__(self, responses: list[dict]):
        self.responses = responses

    async def complete_json(self, system: str, user: str) -> dict:
        del system, user
        return self.responses.pop(0)


def book(name: str = "东方快车谋杀案") -> LibraryBookCandidate:
    return LibraryBookCandidate(
        id=uuid4(),
        name=name,
        authors=["阿加莎·克里斯蒂"],
        category="小说",
        tags=["悬疑", "推理"],
        summary="列车上的经典推理故事。",
        available=True,
        availableCount=2,
        totalCount=3,
    )


def test_high_library_match_skips_external_search(monkeypatch):
    candidate = book()

    async def fail_if_called(query: str):
        raise AssertionError(f"Open Library should not be queried: {query}")

    monkeypatch.setattr("agent_service.library_recommendation._search_open_library", fail_if_called)
    model = StubModel(
        [
            {
                "recommendations": [
                    {"bookId": str(candidate.id), "score": 92, "reason": "悬疑推理高度匹配"}
                ],
                "externalQuery": "mystery",
            }
        ]
    )

    result = asyncio.run(
        recommend_books(
            LibraryRecommendationRequest(requirement="想读反转多的悬疑小说", books=[candidate]),
            model,
        )
    )

    assert len(result) == 1
    assert result[0].source_type == "LIBRARY"
    assert result[0].featured is True
    assert result[0].book_id == candidate.id


def test_external_candidates_are_used_only_from_search_results(monkeypatch):
    candidate = book("普通校园故事")
    external_key = "EXT:/works/OL123W"

    async def external_search(query: str):
        assert query == "locked room mystery"
        return [
            {
                "key": external_key,
                "name": "The Mystery Book",
                "authors": ["A. Writer"],
                "publishedYear": 2020,
                "isbn": "9780000000000",
                "publisher": "Example",
                "language": "eng",
                "tags": ["Mystery"],
                "coverImage": "https://covers.openlibrary.org/example.jpg",
                "externalUrl": "https://openlibrary.org/works/OL123W",
            }
        ]

    monkeypatch.setattr(
        "agent_service.library_recommendation._search_open_library", external_search
    )
    model = StubModel(
        [
            {
                "recommendations": [
                    {"bookId": str(candidate.id), "score": 65, "reason": "部分符合"}
                ],
                "externalQuery": "locked room mystery",
            },
            {
                "query": "locked room mystery",
                "titleQueries": [],
            },
            {
                "recommendations": [
                    {"key": "/works/OL123W", "score": 90, "reason": "更符合密室推理需求"},
                    {"key": "LIB:" + str(candidate.id), "score": 64, "reason": "馆内备选"},
                    {"key": "EXT:/works/INVENTED", "score": 100, "reason": "编造项"},
                ]
            },
        ]
    )

    result = asyncio.run(
        recommend_books(
            LibraryRecommendationRequest(requirement="想读密室推理小说", books=[candidate]),
            model,
        )
    )

    assert [item.key for item in result] == [external_key, "LIB:" + str(candidate.id)]
    assert result[0].source_type == "EXTERNAL"
    assert result[0].reason.startswith("图书馆未找到高度匹配馆藏；")
    assert result[0].external_url.startswith("https://openlibrary.org/")
