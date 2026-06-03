import difflib
from typing import List


def compute_diff(text_left: str, text_right: str) -> List[dict]:
    lines_left = text_left.splitlines(keepends=False)
    lines_right = text_right.splitlines(keepends=False)

    matcher = difflib.SequenceMatcher(None, lines_left, lines_right)
    diff_result = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for idx in range(i2 - i1):
                diff_result.append({
                    "type": "equal",
                    "line_left": i1 + idx + 1,
                    "line_right": j1 + idx + 1,
                    "content_left": lines_left[i1 + idx],
                    "content_right": lines_right[j1 + idx],
                })
        elif tag == "delete":
            for idx in range(i2 - i1):
                diff_result.append({
                    "type": "delete",
                    "line_left": i1 + idx + 1,
                    "line_right": None,
                    "content_left": lines_left[i1 + idx],
                    "content_right": "",
                })
        elif tag == "insert":
            for idx in range(j2 - j1):
                diff_result.append({
                    "type": "add",
                    "line_left": None,
                    "line_right": j1 + idx + 1,
                    "content_left": "",
                    "content_right": lines_right[j1 + idx],
                })
        elif tag == "replace":
            max_len = max(i2 - i1, j2 - j1)
            for idx in range(max_len):
                left_line = lines_left[i1 + idx] if (i1 + idx) < i2 else ""
                right_line = lines_right[j1 + idx] if (j1 + idx) < j2 else ""
                diff_result.append({
                    "type": "change",
                    "line_left": (i1 + idx + 1) if (i1 + idx) < i2 else None,
                    "line_right": (j1 + idx + 1) if (j1 + idx) < j2 else None,
                    "content_left": left_line,
                    "content_right": right_line,
                })

    return diff_result
