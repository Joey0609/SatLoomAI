from __future__ import annotations

from collections import deque


class _Node:
    """Aho-Corasick 自动机节点。"""
    __slots__ = ("children", "fail", "output")

    def __init__(self) -> None:
        self.children: dict[str, _Node] = {}
        self.fail: _Node | None = None
        # 存储在此节点结尾的模式串在原始列表中的索引
        self.output: list[int] = []


class AhoCorasick:
    """Aho-Corasick 多模式串匹配自动机。

    构建时间 O(sum(len(pattern)))，匹配时间 O(len(text) + 匹配数)。
    支持 Unicode（中文等字符无需额外处理）。
    """

    def __init__(self, patterns: list[str]) -> None:
        self._patterns = patterns
        self._root = _Node()
        self._build_trie()
        self._build_fail_links()

    # ── 构建 ─────────────────────────────────────────────────

    def _build_trie(self) -> None:
        for idx, pattern in enumerate(self._patterns):
            node = self._root
            for ch in pattern:
                if ch not in node.children:
                    node.children[ch] = _Node()
                node = node.children[ch]
            node.output.append(idx)

    def _build_fail_links(self) -> None:
        q: deque[_Node] = deque()
        for child in self._root.children.values():
            child.fail = self._root
            q.append(child)

        while q:
            curr = q.popleft()
            for ch, child in curr.children.items():
                # 找 fail 指针
                fail = curr.fail
                while fail is not None and ch not in fail.children:
                    fail = fail.fail
                child.fail = fail.children[ch] if fail else self._root
                # 合并输出
                if child.fail:
                    child.output.extend(child.fail.output)
                q.append(child)

    # ── 搜索 ─────────────────────────────────────────────────

    def search(self, text: str) -> list[tuple[int, int, str]]:
        """返回所有匹配结果。

        Returns:
            list of (start_index, end_index, pattern_text)
        """
        node = self._root
        results: list[tuple[int, int, str]] = []

        for i, ch in enumerate(text):
            # 失配时沿 fail 回溯
            while node is not self._root and ch not in node.children:
                node = node.fail  # type: ignore[assignment]
            if ch in node.children:
                node = node.children[ch]
            else:
                # 仍然在根节点
                continue

            for idx in node.output:
                pat = self._patterns[idx]
                start = i - len(pat) + 1
                results.append((start, i, pat))

        return results

    def find_matched(self, text: str) -> list[str]:
        """仅返回匹配到的去重模式串，按首次出现位置排序。"""
        raw = self.search(text)
        seen: set[str] = set()
        ordered: list[str] = []
        for _start, _end, pat in raw:
            if pat not in seen:
                seen.add(pat)
                ordered.append(pat)
        return ordered
