import pytest

from agent_service.learning_checks import (
    check_generated_counts,
    reference_checks,
    traversal_practice_issues,
)
from agent_service.learning_models import LearningRequest


@pytest.mark.parametrize("claim,valid", [("D E B F C A", True), ("D E B C F A", False)])
def test_traversal_proof_reference_rejects_swapped_subtree(claim, valid):
    issues = traversal_practice_issues(
        dict(
            questionType="PROOF",
            prompt="先序遍历序列为 A B D E C F，中序遍历序列为 D B E A F C。求后序。",
            standardAnswer="后序遍历序列为：" + claim,
        )
    )
    assert bool(issues) is not valid


def test_traversal_choice_correct_option_checked_independently():
    raw = dict(
        questionType="CHOICE",
        prompt="先序遍历序列为ABC，中序遍历序列为BAC，求后序。",
        options=["A. BCA", "B. CBA"],
        standardAnswer="B",
    )
    assert traversal_practice_issues(raw)
    assert not traversal_practice_issues({**raw, "standardAnswer": "A"})


@pytest.mark.parametrize("size", [1, 2, 3, 16, 31, 32])
def test_binary_search_reference_matches_exhaustive_execution(size):
    comparisons = []
    for target in range(-1, size + 1):
        low, high, count = 0, size - 1, 0
        while low <= high:
            middle = (low + high) // 2
            count += 1
            if middle == target:
                break
            if middle < target:
                low = middle + 1
            else:
                high = middle - 1
        comparisons.append(count)
    checks = reference_checks(
        LearningRequest(
            mode="EXPLAIN", course="算法设计与分析", prompt=f"长度为{size}的标准二分查找"
        )
    )
    assert checks["binarySearch"]["worstComparisons"] == max(comparisons)


def test_rule_rejects_incorrect_structured_count_and_final_claim():
    checks = {"binarySearch": {"worstComparisons": 5}}
    assert check_generated_counts({"binarySearchWorstComparisons": 4}, checks)
    assert check_generated_counts(
        {"binarySearchWorstComparisons": 5, "conclusion": "最坏4次比较"}, checks
    )
    assert not check_generated_counts(
        {"binarySearchWorstComparisons": 5, "conclusion": "最坏5次比较"}, checks
    )


def test_best_case_and_latest_length_do_not_trigger_false_rejection():
    checks = reference_checks(
        LearningRequest(
            mode="CORRECT",
            course="算法设计与分析",
            prompt="长度为16的二分查找",
            previousAnswer="最坏5次比较",
            correction="现在改为长度为32，解释最好与最坏情况",
        )
    )
    assert checks["binarySearch"]["worstComparisons"] == 6
    assert not check_generated_counts(
        {"binarySearchWorstComparisons": 6, "answer": "最好1次比较，最坏6次比较"}, checks
    )
