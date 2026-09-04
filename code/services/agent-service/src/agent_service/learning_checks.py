"""Deterministic reference checks; never execute learner-supplied programs."""

import re

from agent_service.learning_models import LearningRequest


def question_only(request: LearningRequest) -> bool:
    """Recognize explicit question-only self tests; mixed explanation requests stay unchanged."""
    latest = request.correction or request.prompt
    exercise = re.search(r"自测|练习|测验|practice|exercise|quiz", latest, re.I)
    hidden = re.search(
        r"(?:不要|不附|不给|别|隐藏|不提供|暂不).*(?:答案|解答)"
        r"|without.*(?:answer|solution)|(?:hide|don't.*give).*answer",
        latest,
        re.I,
    )
    mixed = re.search(r"对比|先.*(?:讲解|解释)|compare|explain.*then", latest, re.I)
    return bool(exercise and hidden and not mixed)


def missing_work_process(text: str) -> bool:
    """Explicit absence is not evidence of a misconception, regardless of string length."""
    return bool(
        re.search(
            r"(?:没有|没写|未写|未提供|不记得|忘记|没有写).*(?:过程|步骤|怎么)"
            r"|(?:过程|步骤).*(?:没有|没写|不记得|忘记)|只(?:记得|写了|知道).*(?:答案|最后)"
            r"|(?:no|without).*(?:working|steps|reasoning)",
            text,
            re.I,
        )
    )


def visible_draft(request: LearningRequest, generated: dict) -> dict:
    """Never expose hidden solution fields for an explicitly question-only request."""
    if not question_only(request):
        checks = reference_checks(request)
        reference = checks.get("binarySearch")
        if reference:
            # Rule evidence is application-owned, not a model's claim about its own checks.
            issues = check_generated_counts(generated, checks)
            generated = {
                **generated,
                "verification": (
                    f"程序规则：数组长度{reference['size']}，{reference['definition']}；"
                    f"最坏比较次数为{reference['worstComparisons']}。"
                    + ("候选次数未通过规则校验。" if issues else "候选次数与规则一致。")
                    + "此项仅核对次数，不代表教材引用或整份解答已通过审查。"
                ),
            }
        return generated
    question = generated.get("selfTestQuestion")
    return {
        "answer": question if isinstance(question, str) else "",
        "steps": [],
        "conclusion": "请先独立作答，提交过程后再核对。",
        "diagnosis": [],
        "correctedPoints": [],
        "limitations": ["AI生成自测题，尚未作答。"],
        "verification": "本轮仅提供题目，未进行作答评估。",
        "selfTestQuestion": question,
    }


def selftest_issues(request: LearningRequest, generated: dict) -> list[str]:
    """Reject a traversal self-test whose given data already states the requested answer."""
    if not question_only(request):
        return []
    question = str(generated.get("answer") or "")
    requested = (request.correction or request.prompt) + question.rsplit("请", 1)[-1]
    requested = requested.replace("先序", "前序")
    given = re.findall(
        r"(先序|前序|中序|后序|层序)遍历(?:序列|结果|顺序)\s*(?:为|是|[:：])", question
    )
    if any(kind.replace("先序", "前序") in requested for kind in given):
        return [
            "自测题题干已直接给出待求遍历序列，泄露答案。请改为明确的父子关系描述，不能给出任何待求序列。"
        ]
    return []


def reference_checks(request: LearningRequest) -> dict:
    turns = [turn.content for turn in request.history if turn.role == "user"] + [request.prompt]
    if request.correction:
        turns.append(request.correction)
    text = "\n".join(turns)
    if not re.search(r"二分查找|折半查找", text):
        return {}
    # A correction can replace the original array length; prefer its latest explicit value.
    size = None
    for turn in reversed(turns):
        if re.search(r"空数组|empty array", turn, re.I):
            size = 0
            break
        matches = re.findall(
            r"(?:长度|大小|size|length|n\s*=)(?:为|是|改为|改成)?\s*(\d+)|(?:改为|改成|设为)\s*(\d+)",
            turn,
            re.I,
        )
        if matches:
            size = int(next(value for value in matches[-1] if value))
            break
        if re.search(r"改|变|instead|change", turn, re.I):
            return {}  # Unknown replacement must not reactivate stale numeric constraints.
    if size is None or not 0 <= size <= 1000000:
        return {}
    return {
        "binarySearch": {
            "size": size,
            "worstComparisons": size.bit_length(),
            "definition": "标准闭区间二分查找，每轮与中间元素的三路比较计一次；单元素仍需比较",
            "formula": "n=0时0次；n>=1时floor(log2(n))+1，不是仅计算减半至1的次数",
            "requiredOutputField": "binarySearchWorstComparisons",
        }
    }


def traversal_practice_issues(raw: dict) -> list[str]:
    """Verify explicit unique-uppercase-node traversal exercises without executing model code."""
    prompt = str(raw.get("prompt") or "")
    sequences = []
    for order in (r"(?:前序|先序)", "中序"):
        match = re.search(order + r"遍历序列(?:为|是)?\s*[:：]?\s*([A-Z][A-Z \t,，、]*)", prompt)
        if match is None:
            return []
        sequences.append(re.sub(r"[^A-Z]", "", match[1]))
    pre, ino = sequences
    if not 1 <= len(pre) <= 26 or len(set(pre)) != len(pre):
        return []
    if len(pre) != len(ino) or set(pre) != set(ino):
        return ["遍历题先序和中序的节点集合不一致"]

    def postorder(first: str, middle: str) -> str:
        if not first:
            return ""
        root = first[0]
        split = middle.index(root)
        return (
            postorder(first[1 : split + 1], middle[:split])
            + postorder(first[split + 1 :], middle[split + 1 :])
            + root
        )

    try:
        expected = postorder(pre, ino)
    except ValueError:
        return ["先序和中序序列不兼容，无法构成同一棵二叉树"]
    if "后序" not in prompt:
        return []
    answer = str(raw.get("standardAnswer") or "")
    if raw.get("questionType", "").upper() == "CHOICE":
        selected = re.match(r"\s*([A-F])(?:\b|[.、:：)）])", answer)
        if selected is None:
            return ["选择题标准答案必须明确正确选项标签"]
        for option in raw.get("options", []):
            if re.match(r"\s*" + selected[1] + r"\s*[.、:：)）]", option):
                content = re.sub(r"^[A-F]\s*[.、:：)）]\s*", "", option.strip())
                if re.sub(r"[ \t,，、]", "", content) != expected:
                    return [f"遍历参考算法校验：后序应为{expected}，正确选项与之不符"]
                return []
        return ["标准答案引用了不存在的选项"]
    claimed = re.findall(
        r"后序(?:遍历)?(?:序列)?(?:为|是)?\s*[:：]?\s*([A-Z][A-Z \t,，、]*)", answer
    )
    if re.fullmatch(r"[A-Z \t,，、]+[。.]?", answer.strip()):
        claimed.append(answer)
    if claimed and any(re.sub(r"[^A-Z]", "", item) != expected for item in claimed):
        return [f"遍历参考算法校验：根据题目先序{pre}与中序{ino}，后序应为{expected}"]
    return []


def check_generated_counts(generated: dict, checks: dict) -> list[str]:
    reference = checks.get("binarySearch")
    if not reference:
        return []
    expected = reference["worstComparisons"]
    count = generated.get("binarySearchWorstComparisons")
    if type(count) is not int or count != expected:
        return [f"规则校验：标准闭区间二分查找最坏比较次数应为{expected}，请声明计数口径。"]
    # Inspect final claims, not quotations of previous mistakes or numbered worked steps.
    final_text = str(generated.get("answer", "")) + str(generated.get("conclusion", ""))
    counts = re.findall(
        r"最坏(?:情况)?(?:下)?(?:需要|为|是|需|最多)?\s*(\d+)\s*次(?:比较|三路比较)", final_text
    )
    if any(int(value) != expected for value in counts):
        return [f"规则校验：最终文字结论与已计算的{expected}次比较矛盾。"]
    explanation = " ".join(
        str(generated.get(key, "")) for key in ("answer", "steps", "conclusion", "limitations")
    )
    if re.search(
        r"(?:标准闭区间)?二分查找要求数组非空|空数组(?:通常)?(?:被视为|属于|是)非法输入",
        explanation,
    ):
        return [
            "空数组是标准二分查找可处理的有效边界，循环不进入；不能断言它是非法输入或算法要求非空"
        ]
    return []


def traversal_sample_issues(raw: dict, cases: list[dict[str, str]]) -> list[str]:
    """Check the explicit n/preorder/inorder -> level-order contract, without executing code."""
    prompt = str(raw.get("prompt") or "")
    if not (
        raw.get("questionType") == "PROGRAMMING"
        and "层序" in prompt
        and re.search(r"(?:第二行|第2行)[^。\n]*[先前]序", prompt)
        and re.search(r"(?:第三行|第3行)[^。\n]*中序", prompt)
    ):
        return []

    bound = re.search(r"1\s*(?:≤|<=)\s*n\s*(?:≤|<=)\s*(\d+)", prompt)
    if bound and int(bound[1]) > 26:
        return ["此重建遍历基础练习请限定1≤n≤26，避免单字符唯一性与递归深度边界冲突"]

    def build(pre: str, ino: str):
        if not pre:
            return None
        split = ino.index(pre[0])
        return (
            pre[0],
            build(pre[1 : split + 1], ino[:split]),
            build(pre[split + 1 :], ino[split + 1 :]),
        )

    issues = []
    for index, case in enumerate(cases, 1):
        lines = case["input"].strip().splitlines()
        if len(lines) != 3 or not lines[0].strip().isdigit():
            continue  # Other input contracts remain under independent semantic review.
        pre, ino = (re.sub(r"\s+", "", line) for line in lines[1:])
        if not re.fullmatch(r"[A-Z]{1,26}", pre):
            continue
        if len(pre) != int(lines[0]) or len(ino) != len(pre) or len(set(pre)) != len(pre):
            issues.append(f"测试样例{index}节点数或唯一性不符合题目")
            continue
        try:
            tree = build(pre, ino)
        except (ValueError, IndexError):
            issues.append(f"测试样例{index}先序与中序不兼容")
            continue
        queue = [tree]
        result = ""
        for node in queue:
            if node:
                result += node[0]
                queue.extend([node[1], node[2]])
        if re.sub(r"\s+", "", case["expectedOutput"]) != result:
            issues.append(f"测试样例{index}层序输出应为{result}，不能作为正确样例保存")
    return issues
