"""
LaTeX Parser — parse a raw .tex file into structured sections
so the Reader Agent can perform multi-pass reading.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Section:
    """A single section extracted from a LaTeX document."""

    title: str
    content: str
    level: int = 1  # 1 = \section, 2 = \subsection, 3 = \subsubsection
    is_appendix: bool = False


@dataclass
class ParsedPaper:
    """Structured representation of a parsed LaTeX paper."""

    raw: str = ""
    abstract: str = ""
    sections: list[Section] = field(default_factory=list)
    appendix_sections: list[Section] = field(default_factory=list)

    # ── Convenience properties for the reading pipeline ──────

    # Names (case-insensitive) that belong to the first-pass reading
    _FIRST_PASS_KEYWORDS: tuple[str, ...] = (
        "introduction",
        "preliminar",
        "background",
        "contribution",
        "limitation",
        "related work",
        "overview",
        "motivation",
    )

    @property
    def first_pass_text(self) -> str:
        """Abstract + Introduction + Preliminaries + Contributions + Limitations."""
        parts: list[str] = []
        if self.abstract:
            parts.append(f"## Abstract\n\n{self.abstract}")

        for sec in self.sections:
            title_lower = sec.title.lower()
            if any(kw in title_lower for kw in self._FIRST_PASS_KEYWORDS):
                parts.append(f"## {sec.title}\n\n{sec.content}")

        return "\n\n---\n\n".join(parts) if parts else self.abstract

    @property
    def main_body_text(self) -> str:
        """Everything except first-pass sections, references, and appendix."""
        parts: list[str] = []
        for sec in self.sections:
            title_lower = sec.title.lower()
            # Skip first-pass sections
            if any(kw in title_lower for kw in self._FIRST_PASS_KEYWORDS):
                continue
            # Skip references
            if "reference" in title_lower or "bibliograph" in title_lower:
                continue
            parts.append(f"## {sec.title}\n\n{sec.content}")

        return "\n\n---\n\n".join(parts)

    @property
    def appendix_text(self) -> str:
        """Appendix sections concatenated."""
        if not self.appendix_sections:
            return ""
        parts = [f"## {sec.title}\n\n{sec.content}" for sec in self.appendix_sections]
        return "\n\n---\n\n".join(parts)

    @property
    def has_appendix(self) -> bool:
        return bool(self.appendix_sections)


# ── Public API ────────────────────────────────────────────────


def parse_latex(tex: str) -> ParsedPaper:
    """
    Parse raw LaTeX source into a ``ParsedPaper``.

    Handles:
    - \\begin{abstract} ... \\end{abstract}
    - \\section{}, \\subsection{}, \\subsubsection{}
    - \\appendix marker
    - \\bibliography / \\begin{thebibliography}
    """
    paper = ParsedPaper(raw=tex)

    # ── 1. Extract abstract ──
    abs_match = re.search(
        r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.DOTALL
    )
    if abs_match:
        paper.abstract = _clean_latex(abs_match.group(1).strip())

    # ── 2. Locate key markers ──
    appendix_pos = _find_marker(tex, r"\\appendix(?:\b|[^a-zA-Z])")
    bib_pos = _find_marker(
        tex,
        r"\\(?:bibliography\{|begin\{thebibliography\}|printbibliography)",
    )
    doc_end_pos = tex.find("\\end{document}")
    if doc_end_pos < 0:
        doc_end_pos = len(tex)

    # ── 3. Extract sections ──
    section_pattern = re.compile(
        r"\\(section|subsection|subsubsection)\{([^}]+)\}"
    )
    matches = list(section_pattern.finditer(tex))

    for i, m in enumerate(matches):
        level_str, title = m.group(1), m.group(2).strip()
        level = {"section": 1, "subsection": 2, "subsubsection": 3}[level_str]
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else doc_end_pos

        # Trim if content extends past bibliography/appendix/end
        for boundary in [bib_pos, doc_end_pos]:
            if boundary and start < boundary < end:
                end = boundary

        content = _clean_latex(tex[start:end].strip())

        sec = Section(title=title, content=content, level=level)

        # Determine if this section is in the appendix region
        if appendix_pos is not None and m.start() >= appendix_pos:
            sec.is_appendix = True
            paper.appendix_sections.append(sec)
        else:
            paper.sections.append(sec)

    return paper


# ── Helpers ───────────────────────────────────────────────────


def _find_marker(tex: str, pattern: str) -> int | None:
    """Return the position of the first regex match, or None."""
    m = re.search(pattern, tex)
    return m.start() if m else None


def _clean_latex(text: str) -> str:
    """Light cleanup of LaTeX content for readability.

    We do NOT strip all LaTeX commands — LLMs read LaTeX fine.
    We only remove very noisy elements.
    """
    # Remove \label{...}
    text = re.sub(r"\\label\{[^}]*\}", "", text)
    # Remove \vspace{...}, \hspace{...}
    text = re.sub(r"\\[vh]space\{[^}]*\}", "", text)
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
