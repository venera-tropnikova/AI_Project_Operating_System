# -*- coding: utf-8 -*-
"""
Confirmed project setup actions for AI POS.

Allowed:
- create archive/ in project root (if missing)
- move confirmed backup files into archive/, preserving relative paths
- create required docs only when real project content_source is provided
- create/update passport and docs from explicit user_info (non-empty fields only)

Never deletes. Never invents content. Never touches Stage Engine / Analyzer /
Passport schema / Governance.
Preview is read-only. setup-status is read-only.
Apply requires confirm=True. Readiness flag is written only after confirmed setup
when the full ready criteria are met.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from project_structure_map import (
    AI_POS_DOC_CHECKS,
    _find_named_file,
    _md_has_substance,
    _passport_has_substance,
    build_structure_map,
)

ALLOWED_SETUP_IDS = frozenset({"folder_archive", "backups_to_archive"})
ARCHIVE_DIR_NAME = "archive"
SUCCESS_MESSAGE = "Проект подготовлен для дальнейшей работы."
NOT_READY_MESSAGE = "Сначала проверьте и настройте проект"
SETUP_FLAG_REL = Path(".ai-pos") / "project_setup.json"
SETUP_FLAG_SCHEMA = "ai-pos-project-setup"
PASSPORT_REL = Path(".ai-pos") / "project_passport.json"
PASSPORT_SCHEMA = "ai-pos.project_passport/v1"
PASSPORT_VERSION = 1

USER_DOC_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("roadmap", "ROADMAP.md", "План (ROADMAP)"),
    ("architecture", "ARCHITECTURE.md", "Устройство (ARCHITECTURE)"),
    ("design_rules", "DESIGN_RULES.md", "Правила дизайна (DESIGN_RULES)"),
    ("decisions", "DECISIONS.md", "Решения (DECISIONS)"),
    ("data_schema", "DATA_SCHEMA.md", "Схема данных (DATA_SCHEMA)"),
)

PASSPORT_FIELD_LABELS = {
    "name": "название проекта",
    "summary": "описание",
    "goal": "цель проекта",
    "audience": "сведения паспорта (аудитория и др.)",
    "expected_result": "ожидаемый результат",
    "status": "статус",
}


def _norm_rel(path: str) -> str:
    return str(path or "").replace("\\", "/").strip().lstrip("/")


def _read_setup_flag(root: Path) -> dict[str, Any]:
    path = root / SETUP_FLAG_REL
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_setup_flag(root: Path, *, prepared: bool) -> bool:
    """Write readiness flag. Does not touch passport/stage/analysis."""
    ai_dir = root / ".ai-pos"
    if not ai_dir.is_dir():
        return False
    payload = {
        "schema": SETUP_FLAG_SCHEMA,
        "version": 1,
        "prepared": bool(prepared),
        "message": SUCCESS_MESSAGE if prepared else None,
    }
    path = ai_dir / "project_setup.json"
    try:
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return True
    except OSError:
        return False


def _is_allowed_setup_action(action: dict[str, Any]) -> bool:
    if not action.get("setup_allowed"):
        return False
    aid = str(action.get("id") or "")
    if aid in ALLOWED_SETUP_IDS:
        return True
    if str(action.get("kind") or "") == "create_doc" and action.get("content_source"):
        return True
    return False


def _missing_required_docs(root: Path) -> list[str]:
    missing: list[str] = []
    for filename, _title, _human in AI_POS_DOC_CHECKS:
        hits = [h for h in _find_named_file(root, filename) if _md_has_substance(root / h)]
        if not hits:
            missing.append(filename)
    return missing


def _mandatory_open_items(diagnostics: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for key in ("can_setup", "needs_review", "insufficient"):
        for item in diagnostics.get(key) or []:
            if isinstance(item, dict) and item.get("mandatory"):
                items.append(item)
    return items


def evaluate_project_ready(
    root: Path,
    *,
    diagnostics: dict[str, Any] | None = None,
    setup_actions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Ready only when ALL approved conditions hold:
    1) required docs present with substance in root/docs/
    2) passport сведения confirmed
    3) no pending confirmed setup_actions
    4) user completed setup (project_setup.json prepared=true)
    5) no mandatory open items in diagnostics buckets
    """
    diag = diagnostics if isinstance(diagnostics, dict) else {}
    actions = [
        a
        for a in (setup_actions if setup_actions is not None else diag.get("setup_actions") or [])
        if isinstance(a, dict) and _is_allowed_setup_action(a)
    ]
    missing_docs = _missing_required_docs(root)
    passport_ok, passport_rel, passport_evidence = _passport_has_substance(root)
    flag = _read_setup_flag(root)
    flag_prepared = bool(flag.get("prepared"))
    mandatory = _mandatory_open_items(diag)

    reasons_ok: list[str] = []
    reasons_block: list[str] = []

    if not missing_docs:
        reasons_ok.append("Обязательные документы найдены в корне или docs/")
    else:
        reasons_block.append(
            "Нет обязательных документов в корне/docs/: " + ", ".join(missing_docs)
        )

    if passport_ok:
        reasons_ok.append(f"Паспорт подтверждён ({passport_rel})")
    else:
        reasons_block.append(
            "Паспорт не подтверждён: нет содержательных сведений"
            + (f" ({'; '.join(passport_evidence[:3])})" if passport_evidence else "")
        )

    if not actions:
        reasons_ok.append("Нет невыполненных обязательных setup_actions")
    else:
        reasons_block.append(
            "Есть невыполненные обязательные действия: "
            + ", ".join(str(a.get("id") or "?") for a in actions)
        )

    docs_and_passport_ok = (not missing_docs) and passport_ok and (not actions)
    if flag_prepared and docs_and_passport_ok:
        reasons_ok.append("Пользователь подтвердил настройку (project_setup.json)")
    elif not flag_prepared:
        reasons_block.append(
            "Нет подтверждённого завершения настройки (.ai-pos/project_setup.json)"
        )
    elif flag_prepared and not docs_and_passport_ok:
        reasons_block.append(
            "Есть project_setup.json, но обязательные документы/сведения ещё не подтверждены"
        )

    # Mandatory items that are not already covered by missing docs / actions lists.
    if mandatory and (missing_docs or not passport_ok or actions):
        titles = [str(m.get("title") or m.get("id") or "") for m in mandatory[:6]]
        if titles:
            reasons_block.append(
                "Обязательные непроверенные пункты диагностики: " + "; ".join(titles)
            )

    ready = docs_and_passport_ok and flag_prepared

    return {
        "ready": ready,
        "prepared": ready,
        "flag_prepared": flag_prepared,
        "missing_docs": missing_docs,
        "passport_ok": passport_ok,
        "setup_actions": actions,
        "mandatory_count": len(mandatory),
        "reasons_ok": reasons_ok,
        "reasons_block": reasons_block,
        "message": SUCCESS_MESSAGE if ready else NOT_READY_MESSAGE,
    }


def get_project_setup_status(project_path: str) -> dict[str, Any]:
    """Fully read-only readiness check. Never writes project_setup.json."""
    raw = str(project_path or "").strip()
    if not raw:
        return {
            "ok": False,
            "wrote": False,
            "ready": False,
            "prepared": False,
            "message": "Не указана рабочая папка проекта.",
            "setup_actions": [],
            "reasons_block": ["Не указана рабочая папка проекта."],
        }
    root = Path(raw)
    if not root.exists() or not root.is_dir():
        return {
            "ok": False,
            "wrote": False,
            "ready": False,
            "prepared": False,
            "message": "Папка проекта не найдена. Проверьте путь в настройках проекта.",
            "setup_actions": [],
            "reasons_block": ["Папка проекта не найдена."],
        }

    review = build_structure_map(raw, include_recommendations=True)
    if not review.get("ok"):
        return {
            "ok": False,
            "wrote": False,
            "ready": False,
            "prepared": False,
            "message": review.get("message") or "Не удалось проверить готовность настройки.",
            "setup_actions": [],
            "reasons_block": [review.get("message") or "Диагностика недоступна."],
        }

    eval_ready = evaluate_project_ready(
        root,
        diagnostics=review.get("diagnostics") or {},
        setup_actions=review.get("setup_actions") or [],
    )
    return {
        "ok": True,
        "wrote": False,
        "ready": bool(eval_ready.get("ready")),
        "prepared": bool(eval_ready.get("prepared")),
        "flag_prepared": bool(eval_ready.get("flag_prepared")),
        "message": eval_ready.get("message"),
        "setup_actions": eval_ready.get("setup_actions") or [],
        "missing_docs": eval_ready.get("missing_docs") or [],
        "passport_ok": bool(eval_ready.get("passport_ok")),
        "reasons_ok": eval_ready.get("reasons_ok") or [],
        "reasons_block": eval_ready.get("reasons_block") or [],
        "project_path": str(root.resolve()),
        "diagnostics": review.get("diagnostics") or {},
    }


def _resolve_under_root(root: Path, rel: str) -> Path | None:
    rel_norm = _norm_rel(rel)
    if not rel_norm or ".." in Path(rel_norm).parts:
        return None
    candidate = (root / rel_norm).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def _load_setup_actions(project_path: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    review = build_structure_map(project_path, include_recommendations=True)
    if not review.get("ok"):
        return review, []
    actions = [
        a
        for a in (review.get("setup_actions") or [])
        if isinstance(a, dict) and _is_allowed_setup_action(a)
    ]
    return review, actions


def _trim_text(value: Any) -> str:
    return str(value or "").strip()


def _text_has_substance(text: str) -> bool:
    body = [
        ln for ln in str(text or "").splitlines() if ln.strip() and not ln.strip().startswith("#")
    ]
    return len(body) >= 2


def normalize_user_info(raw: Any) -> dict[str, str]:
    """Keep only non-empty user-provided strings. No invented defaults."""
    data = raw if isinstance(raw, dict) else {}
    out: dict[str, str] = {}
    for key in (
        "name",
        "goal",
        "description",
        "result",
        "passport",
        "status",
        "roadmap",
        "architecture",
        "design_rules",
        "decisions",
        "data_schema",
    ):
        val = _trim_text(data.get(key))
        if val:
            out[key] = val
    return out


def _read_existing_passport(root: Path) -> dict[str, Any]:
    path = root / PASSPORT_REL
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _passport_payload_from_user_info(
    root: Path, user_info: dict[str, str]
) -> dict[str, Any] | None:
    """Merge only filled user fields into existing passport. Schema unchanged."""
    existing = _read_existing_passport(root)
    mapping = {
        "name": user_info.get("name"),
        "summary": user_info.get("description"),
        "goal": user_info.get("goal"),
        "audience": user_info.get("passport"),
        "expected_result": user_info.get("result"),
        "status": user_info.get("status"),
    }
    if not any(mapping.values()):
        return None

    def pick(key: str) -> str:
        incoming = _trim_text(mapping.get(key))
        if incoming:
            return incoming
        return _trim_text(existing.get(key))

    payload = {
        "schema": PASSPORT_SCHEMA,
        "version": PASSPORT_VERSION,
        "project_id": _trim_text(existing.get("project_id")),
        "name": pick("name"),
        "summary": pick("summary"),
        "goal": pick("goal"),
        "audience": pick("audience"),
        "expected_result": pick("expected_result"),
        "capabilities": existing.get("capabilities")
        if isinstance(existing.get("capabilities"), list)
        else [],
        "status": pick("status"),
        "modules": existing.get("modules") if isinstance(existing.get("modules"), list) else [],
    }
    missing = [
        key
        for key in ("name", "summary", "goal", "audience", "expected_result", "status")
        if not _trim_text(payload.get(key))
    ]
    payload["missing_fields"] = missing
    filled_now = [
        key
        for key in ("name", "summary", "goal", "audience", "expected_result")
        if _trim_text(mapping.get(key))
    ]
    if not filled_now and not any(
        _trim_text(payload.get(k)) for k in ("name", "summary", "goal", "audience", "expected_result")
    ):
        return None
    return payload


def _build_simple_doc(filename: str, body: str) -> str | None:
    text = _trim_text(body)
    if not text:
        return None
    title = filename.replace(".md", "")
    return f"# {title}\n\n{text}\n"


def _md_section_body(text: str, heading_match: str) -> str:
    """Return body of first ##/### section whose heading contains heading_match."""
    lines = str(text or "").splitlines()
    start = -1
    for i, ln in enumerate(lines):
        stripped = ln.strip()
        if stripped.startswith("##") and heading_match.lower() in stripped.lower():
            start = i + 1
            break
    if start < 0:
        return ""
    body: list[str] = []
    for ln in lines[start:]:
        if ln.strip().startswith("## ") or (
            ln.strip().startswith("##") and not ln.strip().startswith("###")
        ):
            break
        body.append(ln)
    return "\n".join(body).strip()


def _first_paragraph_after_title(text: str) -> str:
    lines = str(text or "").splitlines()
    i = 0
    while i < len(lines) and not lines[i].strip().startswith("#"):
        i += 1
    if i < len(lines) and lines[i].strip().startswith("#"):
        i += 1
    chunk: list[str] = []
    while i < len(lines):
        ln = lines[i]
        if ln.strip().startswith("#"):
            break
        if not ln.strip():
            if chunk:
                break
            i += 1
            continue
        chunk.append(ln.strip())
        i += 1
    return " ".join(chunk).strip()


def _extract_readme_context_facts(readme_text: str) -> dict[str, str]:
    """
    Pull only explicitly stated facts from README.
    Does not invent goal, audience, or expected_result.
    """
    text = str(readme_text or "").strip()
    facts: dict[str, str] = {}
    if not text:
        return facts

    for ln in text.splitlines():
        if ln.startswith("# "):
            name = ln[2:].strip()
            if name:
                facts["name"] = name
            break

    purpose = _first_paragraph_after_title(text)
    if purpose:
        facts["purpose"] = purpose

    # Technologies: only from lead/purpose wording, not from shell examples later.
    tech_scan = purpose or text.split("##", 1)[0]
    tech: list[str] = []
    for token in ("HTML", "CSS", "JavaScript"):
        if token in tech_scan and token not in tech:
            tech.append(token)
    if "localStorage" in text and "localStorage" not in tech:
        # Confirmed in README features list
        tech.append("localStorage")
    if tech:
        facts["technologies"] = "\n".join(f"- {t}" for t in tech)

    # Project type: only phrases that are explicitly present.
    type_bits: list[str] = []
    low = text.lower()
    if "портфолио" in low:
        type_bits.append("портфолио")
    if "адаптивн" in low:
        type_bits.append("адаптивный сайт")
    if "github pages" in low:
        type_bits.append("публикация через GitHub Pages")
    if type_bits:
        # Keep order, unique
        seen: set[str] = set()
        ordered = []
        for bit in type_bits:
            if bit not in seen:
                seen.add(bit)
                ordered.append(bit)
        facts["project_type"] = "; ".join(ordered)

    constraints: list[str] = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s or s.startswith("#") or s.startswith("```") or s.startswith("- [ ]"):
            continue
        low_s = s.lower()
        if low_s.startswith("без ") or "без react" in low_s:
            # Keep only the explicit "Без …" clause, not the rest of the sentence.
            clause = s.split(".")[0].strip()
            if clause.lower().startswith("без ") or "без react" in clause.lower():
                constraints.append(clause)
    if constraints:
        uniq: list[str] = []
        for c in constraints:
            if c not in uniq:
                uniq.append(c)
        facts["constraints"] = "\n".join(f"- {c}" for c in uniq[:4])

    run_body = _md_section_body(text, "Локальный запуск")
    if run_body:
        run_lines: list[str] = []
        for ln in run_body.splitlines():
            s = ln.strip()
            if not s or s.startswith("#"):
                continue
            if s.startswith("```"):
                continue
            # Keep short factual lines and commands, skip long howto fluff selectively
            if s.startswith("python ") or s.startswith("npx ") or s.startswith("`http"):
                run_lines.append(s.strip("`"))
            elif "index.html" in s or "локальн" in s.lower() or "браузере" in s.lower():
                run_lines.append(s)
            elif s.startswith("Вариант") or s.startswith("###"):
                run_lines.append(s.lstrip("# ").strip())
        # Fallback: first 6 non-empty content lines of the section
        if len(run_lines) < 2:
            run_lines = [
                ln.strip()
                for ln in run_body.splitlines()
                if ln.strip() and not ln.strip().startswith("```") and not ln.strip().startswith("#")
            ][:6]
        if run_lines:
            facts["run"] = "\n".join(run_lines[:10])

    pub_body = _md_section_body(text, "Публикация")
    if pub_body:
        pub_lines: list[str] = []
        for ln in pub_body.splitlines():
            s = ln.strip()
            if not s or s.startswith("```") or s.startswith("#"):
                continue
            if s.startswith("- [ ]"):
                continue
            # Numbered steps and explicit URL pattern / relative paths note
            if s[0].isdigit() or s.startswith("`https") or "относительн" in s.lower():
                pub_lines.append(s)
        if len(pub_lines) < 2:
            pub_lines = [
                ln.strip()
                for ln in pub_body.splitlines()
                if ln.strip()
                and not ln.strip().startswith("```")
                and not ln.strip().startswith("#")
                and not ln.strip().startswith("- [ ]")
            ][:8]
        if pub_lines:
            facts["publish"] = "\n".join(pub_lines[:10])

    return facts


def _read_context_source_text(root: Path, source_rel: str = "") -> tuple[str, str]:
    """Return (text, source_label). Prefer explicit source_rel, else README."""
    source_used = _norm_rel(source_rel)
    if source_used:
        src = _resolve_under_root(root, source_used)
        if src is not None and src.is_file():
            try:
                if src.suffix.lower() == ".json":
                    data = json.loads(src.read_text(encoding="utf-8"))
                    if isinstance(data, dict):
                        # Only confirmed filled passport fields — not a README dump.
                        return json.dumps(data, ensure_ascii=False), source_used
                raw = src.read_text(encoding="utf-8", errors="ignore").strip()
                return raw, source_used
            except (OSError, UnicodeError, json.JSONDecodeError):
                pass
    for readme_name in ("README.md", "readme.md", "README.txt"):
        path = root / readme_name
        if path.is_file() and _md_has_substance(path):
            try:
                return path.read_text(encoding="utf-8", errors="ignore").strip(), readme_name
            except (OSError, UnicodeError):
                continue
    return "", ""


def _facts_from_passport_json(raw_json: str) -> dict[str, str]:
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    facts: dict[str, str] = {}
    if _trim_text(data.get("name")):
        facts["name"] = _trim_text(data.get("name"))
    if _trim_text(data.get("summary")):
        facts["purpose"] = _trim_text(data.get("summary"))
    # goal/audience/expected_result are user-confirmed passport fields when filled
    if _trim_text(data.get("goal")):
        facts["goal"] = _trim_text(data.get("goal"))
    if _trim_text(data.get("audience")):
        facts["audience"] = _trim_text(data.get("audience"))
    if _trim_text(data.get("expected_result")):
        facts["expected_result"] = _trim_text(data.get("expected_result"))
    return facts


def _project_context_sufficient(sections: list[dict[str, str]]) -> bool:
    """Reject formal stubs: need name + purpose and at least two more fact sections."""
    keys = {str(s.get("key") or "") for s in sections if _trim_text(s.get("text"))}
    if "name" not in keys or "purpose" not in keys:
        return False
    extra = keys & {"project_type", "technologies", "run", "publish", "constraints", "goal"}
    return len(extra) >= 2


def prepare_project_context(
    root: Path, *, source_rel: str = "", user_info: dict[str, str] | None = None
) -> dict[str, Any]:
    """
    Build PROJECT_CONTEXT from extracted facts only.
    README is a fact source, never pasted in full.
    """
    info = user_info or {}
    source_text, source_label = _read_context_source_text(root, source_rel)
    readme_facts: dict[str, str] = {}
    fact_source = "README"
    if source_text:
        if source_label.lower().endswith(".json"):
            readme_facts = _facts_from_passport_json(source_text)
            fact_source = (
                "паспорт проекта" if "passport" in source_label.lower() else source_label
            )
        else:
            readme_facts = _extract_readme_context_facts(source_text)
            fact_source = "README"

    # User-confirmed fields (form). Never invent.
    user_goal = _trim_text(info.get("goal"))
    user_purpose = _trim_text(info.get("description"))
    user_result = _trim_text(info.get("result"))
    user_audience = _trim_text(info.get("passport"))
    user_name = _trim_text(info.get("name"))

    sections: list[dict[str, str]] = []

    def add(key: str, title: str, text: str, source: str) -> None:
        val = _trim_text(text)
        src = _trim_text(source)
        if not val or not src:
            return
        sections.append({"key": key, "title": title, "text": val, "source": src})

    if user_name:
        add("name", "Название", user_name, "сведения пользователя")
    elif readme_facts.get("name"):
        add("name", "Название", readme_facts["name"], fact_source)

    if user_purpose:
        add("purpose", "Назначение проекта", user_purpose, "сведения пользователя")
    elif readme_facts.get("purpose"):
        add("purpose", "Назначение проекта", readme_facts["purpose"], fact_source)

    if readme_facts.get("project_type"):
        add("project_type", "Тип проекта", readme_facts["project_type"], fact_source)
    if readme_facts.get("technologies"):
        add("technologies", "Технологии", readme_facts["technologies"], fact_source)
    if readme_facts.get("run"):
        add("run", "Способ запуска", readme_facts["run"], fact_source)
    if readme_facts.get("publish"):
        add("publish", "Способ публикации", readme_facts["publish"], fact_source)
    if readme_facts.get("constraints"):
        add("constraints", "Подтверждённые ограничения", readme_facts["constraints"], fact_source)

    if user_goal:
        add("goal", "Цель проекта", user_goal, "сведения пользователя")
    elif readme_facts.get("goal"):
        add("goal", "Цель проекта", readme_facts["goal"], fact_source)

    if user_audience:
        add("audience", "Аудитория", user_audience, "сведения пользователя")
    elif readme_facts.get("audience"):
        add("audience", "Аудитория", readme_facts["audience"], fact_source)

    if user_result:
        add("expected_result", "Ожидаемый результат", user_result, "сведения пользователя")
    elif readme_facts.get("expected_result"):
        add(
            "expected_result",
            "Ожидаемый результат",
            readme_facts["expected_result"],
            fact_source,
        )

    still_needed: list[str] = []
    if not any(s.get("key") == "goal" for s in sections):
        still_needed.append("цель проекта")
    if not any(s.get("key") == "audience" for s in sections):
        still_needed.append("аудитория")
    if not any(s.get("key") == "expected_result" for s in sections):
        still_needed.append("ожидаемый результат")

    ok = _project_context_sufficient(sections)
    content = None
    if ok:
        parts = ["# PROJECT_CONTEXT", ""]
        for sec in sections:
            parts.append(f"## {sec['title']}")
            parts.append(f"Источник: {sec['source']}")
            parts.append("")
            parts.append(sec["text"])
            parts.append("")
        content = "\n".join(parts).rstrip() + "\n"

    section_sources = {
        sec["title"]: sec["source"] for sec in sections
    }
    return {
        "ok": ok,
        "content": content,
        "sections": sections,
        "section_sources": section_sources,
        "still_needed": still_needed,
        "source_label": source_label or "",
        "detail": (
            "Создать docs/PROJECT_CONTEXT.md из извлечённых фактов"
            if ok
            else "PROJECT_CONTEXT.md не создаётся: после извлечения фактов заготовка недостаточна"
        ),
    }


def _build_project_context_content(
    root: Path, *, source_rel: str = "", user_info: dict[str, str] | None = None
) -> str | None:
    prepared = prepare_project_context(root, source_rel=source_rel, user_info=user_info)
    return prepared.get("content") if prepared.get("ok") else None


def _build_doc_content(root: Path, filename: str, source_rel: str) -> str | None:
    if filename.lower() == "project_context.md":
        return _build_project_context_content(root, source_rel=source_rel)
    src = _resolve_under_root(root, source_rel)
    if src is None or not src.is_file():
        return None
    try:
        if src.suffix.lower() == ".json":
            data = json.loads(src.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return None
            lines = [f"# {filename.replace('.md', '')}", ""]
            for key in ("name", "summary", "goal", "audience", "expected_result"):
                val = data.get(key)
                if isinstance(val, str) and val.strip():
                    lines.append(f"## {key}")
                    lines.append(val.strip())
                    lines.append("")
            body = "\n".join(lines).strip()
            return body + "\n" if body else None
        raw = src.read_text(encoding="utf-8", errors="ignore").strip()
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    if not raw:
        return None
    return None


def _doc_already_present(root: Path, filename: str) -> bool:
    hits = [h for h in _find_named_file(root, filename) if _md_has_substance(root / h)]
    return bool(hits)


def _build_user_info_changes(
    root: Path, user_info: dict[str, str], *, existing_targets: set[str]
) -> tuple[list[dict[str, Any]], list[str]]:
    """Build passport/doc changes from filled fields only. Returns (changes, still_needed)."""
    changes: list[dict[str, Any]] = []
    still_needed: list[str] = []
    taken = set(existing_targets)

    passport_payload = _passport_payload_from_user_info(root, user_info)
    if passport_payload:
        field_preview = {
            label: passport_payload[key]
            for key, label in (
                ("name", "name"),
                ("summary", "summary"),
                ("goal", "goal"),
                ("audience", "audience"),
                ("expected_result", "expected_result"),
                ("status", "status"),
            )
            if _trim_text(passport_payload.get(key))
        }
        # Status is schema-listed but not required for passport substance / ready.
        missing_labels = [
            PASSPORT_FIELD_LABELS[k]
            for k in (passport_payload.get("missing_fields") or [])
            if k in PASSPORT_FIELD_LABELS and k != "status"
        ]
        changes.append(
            {
                "id": "write_passport_user_info",
                "action": "write_passport",
                "path": str(PASSPORT_REL).replace("\\", "/"),
                "from": "user_info",
                "to": str(PASSPORT_REL).replace("\\", "/"),
                "ok": True,
                "detail": "Обновить паспорт проекта из заполненных сведений",
                "passport": passport_payload,
                "content_preview": field_preview,
                "still_missing_in_passport": missing_labels,
            }
        )
        for label in missing_labels:
            item = f"паспорт: {label}"
            if item not in still_needed:
                still_needed.append(item)
    else:
        passport_ok, _, _ = _passport_has_substance(root)
        if not passport_ok:
            still_needed.append("паспорт проекта (цель, описание, результат или сведения паспорта)")

    # PROJECT_CONTEXT from extracted facts (README and/or form) — never full README dump
    ctx_target = "docs/PROJECT_CONTEXT.md"
    if not _doc_already_present(root, "PROJECT_CONTEXT.md") and ctx_target not in taken:
        prepared = prepare_project_context(root, user_info=user_info)
        for item in prepared.get("still_needed") or []:
            if item not in still_needed:
                still_needed.append(item)
        if prepared.get("ok") and prepared.get("content"):
            src_set = sorted(
                {
                    str(s.get("source") or "")
                    for s in (prepared.get("sections") or [])
                    if s.get("source")
                }
            )
            changes.append(
                {
                    "id": "create_doc_project_context_user_info",
                    "action": "create_doc",
                    "path": ctx_target,
                    "from": " + ".join(src_set) if src_set else "extracted_facts",
                    "to": ctx_target,
                    "ok": True,
                    "detail": prepared.get("detail")
                    or f"Создать {ctx_target} из извлечённых фактов",
                    "filename": "PROJECT_CONTEXT.md",
                    "content_source": "extracted_facts",
                    "content": prepared.get("content"),
                    "content_preview": prepared.get("content"),
                    "section_sources": prepared.get("section_sources") or {},
                    "context_sections": prepared.get("sections") or [],
                }
            )
            taken.add(ctx_target)
        else:
            msg = "PROJECT_CONTEXT.md (недостаточно подтверждённых фактов для создания)"
            if msg not in still_needed:
                still_needed.append(msg)

    for field_key, filename, human in USER_DOC_FIELDS:
        target = f"docs/{filename}"
        body = user_info.get(field_key, "")
        if _doc_already_present(root, filename):
            continue
        if target in taken:
            continue
        if not body:
            still_needed.append(human)
            continue
        content = _build_simple_doc(filename, body)
        if not content or not _text_has_substance(content):
            still_needed.append(
                f"{human} — текст слишком короткий (нужно не менее двух содержательных строк)"
            )
            continue
        changes.append(
            {
                "id": f"create_doc_{filename.lower().replace('.', '_')}_user_info",
                "action": "create_doc",
                "path": target,
                "from": "user_info",
                "to": target,
                "ok": True,
                "detail": f"Создать {target} из сведений формы",
                "filename": filename,
                "content_source": "user_info",
                "content": content,
                "content_preview": content,
            }
        )
        taken.add(target)

    return changes, still_needed


def _enrich_create_doc_with_user_info(
    root: Path, change: dict[str, Any], user_info: dict[str, str]
) -> dict[str, Any]:
    """Rebuild PROJECT_CONTEXT from extracted facts (+ optional form fields)."""
    if change.get("action") != "create_doc":
        return change
    filename = str(change.get("filename") or Path(str(change.get("to") or "")).name)
    if filename.lower() != "project_context.md":
        return change
    prepared = prepare_project_context(
        root,
        source_rel=str(change.get("content_source") or ""),
        user_info=user_info,
    )
    enriched = dict(change)
    enriched["still_needed_context"] = list(prepared.get("still_needed") or [])
    enriched["section_sources"] = prepared.get("section_sources") or {}
    enriched["context_sections"] = prepared.get("sections") or []
    if prepared.get("ok") and prepared.get("content"):
        enriched["ok"] = True
        enriched["content"] = prepared.get("content")
        enriched["content_preview"] = prepared.get("content")
        enriched["detail"] = prepared.get("detail") or enriched.get("detail")
        src_set = sorted(
            {
                str(s.get("source") or "")
                for s in (prepared.get("sections") or [])
                if s.get("source")
            }
        )
        if src_set:
            enriched["from"] = " + ".join(src_set)
        return enriched
    enriched["ok"] = False
    enriched["content"] = None
    enriched["content_preview"] = None
    enriched["detail"] = prepared.get("detail") or (
        "PROJECT_CONTEXT.md не создаётся: недостаточно подтверждённых фактов"
    )
    return enriched


def _build_changes(root: Path, actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    seen: set[str] = set()

    for action in actions:
        aid = str(action.get("id") or "")
        if aid == "folder_archive":
            key = "create:archive"
            if key in seen:
                continue
            seen.add(key)
            archive_abs = root / ARCHIVE_DIR_NAME
            changes.append(
                {
                    "id": aid,
                    "action": "create_folder",
                    "path": ARCHIVE_DIR_NAME,
                    "from": None,
                    "to": ARCHIVE_DIR_NAME,
                    "exists": archive_abs.is_dir(),
                    "detail": (
                        "Папка archive уже есть — создание будет пропущено."
                        if archive_abs.is_dir()
                        else "Будет создана папка archive в корне проекта."
                    ),
                }
            )
            continue

        if aid == "backups_to_archive":
            for src_rel in action.get("paths") or []:
                src_norm = _norm_rel(str(src_rel))
                if not src_norm:
                    continue
                if src_norm == ARCHIVE_DIR_NAME or src_norm.startswith(ARCHIVE_DIR_NAME + "/"):
                    continue
                dst_norm = f"{ARCHIVE_DIR_NAME}/{src_norm}"
                key = f"move:{src_norm}->{dst_norm}"
                if key in seen:
                    continue
                seen.add(key)
                src_abs = _resolve_under_root(root, src_norm)
                dst_abs = _resolve_under_root(root, dst_norm)
                if src_abs is None or dst_abs is None:
                    changes.append(
                        {
                            "id": aid,
                            "action": "move",
                            "path": src_norm,
                            "from": src_norm,
                            "to": dst_norm,
                            "ok": False,
                            "detail": "Небезопасный путь — перенос будет пропущен.",
                        }
                    )
                    continue
                if not src_abs.is_file():
                    changes.append(
                        {
                            "id": aid,
                            "action": "move",
                            "path": src_norm,
                            "from": src_norm,
                            "to": dst_norm,
                            "ok": False,
                            "detail": "Исходный файл не найден — перенос будет пропущен.",
                        }
                    )
                    continue
                if dst_abs.exists():
                    changes.append(
                        {
                            "id": aid,
                            "action": "move",
                            "path": src_norm,
                            "from": src_norm,
                            "to": dst_norm,
                            "ok": False,
                            "detail": (
                                "В archive уже есть файл по этому пути — "
                                "перенос будет пропущен (ничего не удаляется)."
                            ),
                        }
                    )
                    continue
                changes.append(
                    {
                        "id": aid,
                        "action": "move",
                        "path": src_norm,
                        "from": src_norm,
                        "to": dst_norm,
                        "ok": True,
                        "detail": f"Перенос: {src_norm} → {dst_norm}",
                    }
                )
            continue

        if str(action.get("kind") or "") == "create_doc":
            filename = str(action.get("filename") or Path(str(action.get("target") or "")).name)
            target = _norm_rel(str(action.get("target") or f"docs/{filename}"))
            source = _norm_rel(str(action.get("content_source") or ""))
            key = f"create_doc:{target}"
            if key in seen:
                continue
            seen.add(key)
            dst = _resolve_under_root(root, target)
            prepared: dict[str, Any] | None = None
            content: str | None
            if filename.lower() == "project_context.md":
                prepared = prepare_project_context(root, source_rel=source)
                content = prepared.get("content") if prepared.get("ok") else None
            else:
                content = _build_doc_content(root, filename, source) if source else None
            if not content or dst is None:
                fail = {
                    "id": aid,
                    "action": "create_doc",
                    "path": target,
                    "from": source or None,
                    "to": target,
                    "ok": False,
                    "detail": (
                        (prepared or {}).get("detail")
                        if prepared is not None
                        else (
                            "Недостаточно реальных данных для создания документа — "
                            "пустой файл создаваться не будет."
                        )
                    ),
                    "filename": filename,
                    "content_source": source,
                }
                if prepared is not None:
                    fail["still_needed_context"] = list(prepared.get("still_needed") or [])
                    fail["section_sources"] = prepared.get("section_sources") or {}
                    fail["context_sections"] = prepared.get("sections") or []
                changes.append(fail)
                continue
            if dst.exists():
                changes.append(
                    {
                        "id": aid,
                        "action": "create_doc",
                        "path": target,
                        "from": source,
                        "to": target,
                        "ok": False,
                        "detail": "Файл уже существует — перезапись не выполняется.",
                        "filename": filename,
                        "content_source": source,
                    }
                )
                continue
            item = {
                "id": aid,
                "action": "create_doc",
                "path": target,
                "from": source,
                "to": target,
                "ok": True,
                "detail": (
                    (prepared or {}).get("detail")
                    if prepared is not None
                    else f"Создать {target} из «{source}»"
                ),
                "filename": filename,
                "content_source": source,
                "content": content,
                "content_preview": content,
            }
            if prepared is not None:
                item["still_needed_context"] = list(prepared.get("still_needed") or [])
                item["section_sources"] = prepared.get("section_sources") or {}
                item["context_sections"] = prepared.get("sections") or []
                src_set = sorted(
                    {
                        str(s.get("source") or "")
                        for s in (prepared.get("sections") or [])
                        if s.get("source")
                    }
                )
                if src_set:
                    item["from"] = " + ".join(src_set)
            changes.append(item)

    return changes


def preview_project_setup(
    project_path: str, user_info: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Read-only preview of confirmed setup actions (+ optional user_info). Never writes."""
    raw = str(project_path or "").strip()
    info = normalize_user_info(user_info)
    if not raw:
        return {
            "ok": False,
            "wrote": False,
            "message": "Не указана рабочая папка проекта.",
            "changes": [],
            "still_needed": [],
        }
    root = Path(raw)
    if not root.exists() or not root.is_dir():
        return {
            "ok": False,
            "wrote": False,
            "message": "Папка проекта не найдена. Проверьте путь в настройках проекта.",
            "changes": [],
            "still_needed": [],
        }

    review, actions = _load_setup_actions(raw)
    if not review.get("ok"):
        return {
            "ok": False,
            "wrote": False,
            "message": review.get("message") or "Не удалось подготовить предпросмотр настройки.",
            "changes": [],
            "still_needed": [],
        }

    changes = _build_changes(root, actions)
    changes = [_enrich_create_doc_with_user_info(root, c, info) for c in changes]
    existing_targets = {
        _norm_rel(str(c.get("to") or c.get("path") or ""))
        for c in changes
        if c.get("action") == "create_doc" and c.get("ok") is not False
    }
    user_changes, still_needed = _build_user_info_changes(
        root, info, existing_targets=existing_targets
    )
    changes.extend(user_changes)

    for c in changes:
        for item in c.get("still_needed_context") or []:
            if item and item not in still_needed:
                still_needed.append(item)

    # If PROJECT_CONTEXT will be created, drop generic "insufficient" placeholders for it
    if any(
        c.get("action") == "create_doc"
        and str(c.get("filename") or "").lower() == "project_context.md"
        and c.get("ok") is not False
        for c in changes
    ):
        still_needed = [
            s
            for s in still_needed
            if not str(s).startswith("PROJECT_CONTEXT.md")
        ]

    actionable = [
        c
        for c in changes
        if (c.get("action") == "create_folder" and not c.get("exists"))
        or (
            c.get("action") in {"move", "create_doc", "write_passport"}
            and c.get("ok") is not False
        )
    ]
    status = evaluate_project_ready(
        root,
        diagnostics=review.get("diagnostics") or {},
        setup_actions=actions,
    )

    # Public preview: omit full content from transport noise? Keep content_preview, strip raw content duplicate size - keep both for apply rebuild
    public_changes = []
    for c in changes:
        item = dict(c)
        if "content" in item and "content_preview" not in item and isinstance(item.get("content"), str):
            item["content_preview"] = item["content"]
        public_changes.append(item)

    return {
        "ok": True,
        "wrote": False,
        "message": None,
        "project_path": str(root.resolve()),
        "setup_actions": actions,
        "changes": public_changes,
        "still_needed": still_needed,
        "user_info_applied": sorted(info.keys()),
        "actionable_count": len(actionable),
        "requires_confirm": True,
        "ready": bool(status.get("ready")),
        "reasons_block": status.get("reasons_block") or [],
        "confirm_hint": (
            "Ниже точный список изменений и сведения, которые попадут в файлы. "
            "Запись начнётся только после подтверждения. "
            "Пустые и неподтверждённые поля не используются."
        ),
    }


def apply_project_setup(
    project_path: str,
    *,
    confirm: bool = False,
    user_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Apply only confirmed setup actions after explicit confirm=True.
    Optional user_info writes passport/docs from filled fields only.
    """
    if not confirm:
        return {
            "ok": False,
            "wrote": False,
            "message": "Настройка не выполнена: требуется явное подтверждение.",
            "changes": [],
        }

    info = normalize_user_info(user_info)
    preview = preview_project_setup(project_path, user_info=info)
    if not preview.get("ok"):
        return preview

    root = Path(str(preview.get("project_path") or project_path))
    changes = list(preview.get("changes") or [])
    applied: list[dict[str, Any]] = []
    errors: list[str] = []

    for change in changes:
        if change.get("action") != "create_folder":
            continue
        rel = _norm_rel(str(change.get("to") or change.get("path") or ""))
        if rel != ARCHIVE_DIR_NAME:
            errors.append("Разрешено создавать только папку archive.")
            continue
        target = _resolve_under_root(root, ARCHIVE_DIR_NAME)
        if target is None:
            errors.append("Не удалось безопасно определить путь archive.")
            continue
        try:
            if target.is_dir():
                applied.append({**change, "status": "skipped", "detail": "Папка archive уже существует."})
            else:
                target.mkdir(parents=False, exist_ok=False)
                applied.append({**change, "status": "done", "detail": "Создана папка archive."})
        except OSError:
            errors.append("Не удалось создать папку archive.")
            applied.append({**change, "status": "error", "detail": "Не удалось создать папку."})

    for change in changes:
        if change.get("action") != "move":
            continue
        if change.get("ok") is False:
            applied.append({**change, "status": "skipped", "detail": change.get("detail") or "Перенос пропущен."})
            continue
        src_rel = _norm_rel(str(change.get("from") or ""))
        dst_rel = _norm_rel(str(change.get("to") or ""))
        if not src_rel or not dst_rel.startswith(ARCHIVE_DIR_NAME + "/"):
            errors.append(f"Недопустимый путь переноса: {src_rel} → {dst_rel}")
            continue
        src_abs = _resolve_under_root(root, src_rel)
        dst_abs = _resolve_under_root(root, dst_rel)
        if src_abs is None or dst_abs is None:
            errors.append(f"Небезопасный путь: {src_rel}")
            continue
        if not src_abs.is_file():
            errors.append(f"Файл не найден: {src_rel}")
            applied.append({**change, "status": "error", "detail": "Исходный файл не найден."})
            continue
        if dst_abs.exists():
            applied.append(
                {
                    **change,
                    "status": "skipped",
                    "detail": "Цель уже существует — файл не перезаписывался.",
                }
            )
            continue
        try:
            dst_abs.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_abs), str(dst_abs))
            applied.append(
                {
                    **change,
                    "status": "done",
                    "detail": f"Перенесено: {src_rel} → {dst_rel}",
                }
            )
        except OSError:
            errors.append(f"Не удалось перенести: {src_rel}")
            applied.append({**change, "status": "error", "detail": "Ошибка переноса."})

    for change in changes:
        if change.get("action") != "write_passport":
            continue
        if change.get("ok") is False:
            applied.append(
                {
                    **change,
                    "status": "skipped",
                    "detail": change.get("detail") or "Паспорт не обновлён.",
                }
            )
            continue
        payload = change.get("passport")
        if not isinstance(payload, dict):
            payload = _passport_payload_from_user_info(root, info)
        if not isinstance(payload, dict):
            errors.append("Нет данных для записи паспорта.")
            applied.append({**change, "status": "error", "detail": "Нет данных паспорта."})
            continue
        dst = root / PASSPORT_REL
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            applied.append(
                {
                    **change,
                    "status": "done",
                    "detail": "Паспорт проекта обновлён.",
                    "passport": None,
                    "content_preview": None,
                }
            )
        except OSError:
            errors.append("Не удалось записать паспорт проекта.")
            applied.append({**change, "status": "error", "detail": "Ошибка записи паспорта."})

    for change in changes:
        if change.get("action") != "create_doc":
            continue
        if change.get("ok") is False:
            applied.append(
                {
                    **change,
                    "status": "skipped",
                    "detail": change.get("detail") or "Создание документа пропущено.",
                }
            )
            continue
        target_rel = _norm_rel(str(change.get("to") or ""))
        content = change.get("content")
        filename = str(change.get("filename") or Path(target_rel).name)
        if not isinstance(content, str) or not content.strip():
            source = str(change.get("content_source") or "")
            if source == "user_info" or source.endswith("user_info"):
                if filename.lower() == "project_context.md":
                    content = _build_project_context_content(root, user_info=info)
                else:
                    field_map = {fn.lower(): fk for fk, fn, _h in USER_DOC_FIELDS}
                    field_key = field_map.get(filename.lower())
                    content = (
                        _build_simple_doc(filename, info.get(field_key, ""))
                        if field_key
                        else None
                    )
            else:
                content = _build_doc_content(root, filename, source)
                if filename.lower() == "project_context.md" and info:
                    content = _build_project_context_content(
                        root, source_rel=source, user_info=info
                    )
        dst = _resolve_under_root(root, target_rel)
        if dst is None or not content or not str(content).strip():
            errors.append(f"Недостаточно данных для создания: {target_rel}")
            applied.append({**change, "status": "error", "detail": "Нет реальных данных."})
            continue
        if dst.exists():
            applied.append(
                {
                    **change,
                    "status": "skipped",
                    "detail": "Файл уже существует — не перезаписывался.",
                }
            )
            continue
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(str(content), encoding="utf-8")
            applied.append(
                {
                    **change,
                    "status": "done",
                    "detail": f"Создан документ: {target_rel}",
                    "content": None,
                    "content_preview": None,
                }
            )
        except OSError:
            errors.append(f"Не удалось создать: {target_rel}")
            applied.append({**change, "status": "error", "detail": "Ошибка создания файла."})

    review = build_structure_map(str(root), include_recommendations=True)
    remaining = [
        a
        for a in (review.get("setup_actions") or [])
        if isinstance(a, dict) and _is_allowed_setup_action(a)
    ]
    hard_fail = bool(errors) or any(a.get("status") == "error" for a in applied)
    actions_done = any(a.get("status") == "done" for a in applied)

    # Mark user-confirmed setup completion only when apply finished without hard fail
    # and there was something applied or skipped successfully (user confirmed the step).
    confirmed_step = (not hard_fail) and (
        actions_done
        or any(a.get("status") in {"done", "skipped"} for a in applied)
        or not changes
    )
    if confirmed_step and (root / ".ai-pos").is_dir():
        # Provisional flag: user confirmed setup step. Final ready still needs docs/passport.
        _write_setup_flag(root, prepared=True)

    status = evaluate_project_ready(
        root,
        diagnostics=review.get("diagnostics") or {},
        setup_actions=remaining,
    )
    ready = bool(status.get("ready"))
    # If ready criteria not met, do not claim full success message.
    if ready:
        message = SUCCESS_MESSAGE
    elif hard_fail:
        message = (
            "Не удалось полностью выполнить настройку. "
            "Файлы не удалялись. Можно повторить проверку."
        )
    elif confirmed_step:
        message = (
            "Подтверждённые действия выполнены, но проект ещё не подготовлен: "
            + "; ".join((status.get("reasons_block") or [])[:3])
        )
    else:
        message = "Подтверждённые действия настройки не выполнены."

    return {
        "ok": True,
        "wrote": actions_done or (confirmed_step and bool(_read_setup_flag(root).get("prepared"))),
        "message": message,
        "prepared": ready,
        "ready": ready,
        "flag_prepared": bool(status.get("flag_prepared")),
        "reasons_ok": status.get("reasons_ok") or [],
        "reasons_block": status.get("reasons_block") or [],
        "missing_docs": status.get("missing_docs") or [],
        "project_path": str(root.resolve()),
        "applied": [{k: v for k, v in a.items() if k != "content"} for a in applied],
        "errors": errors,
        "diagnostics": review.get("diagnostics") or {},
        "recommendations": review.get("recommendations") or [],
        "setup_actions": remaining,
        "folder_count": review.get("folder_count"),
        "file_count": review.get("file_count"),
        "tree": review.get("tree"),
        "categories": review.get("categories"),
        "truncated": review.get("truncated"),
        "user_sections": review.get("user_sections"),
    }
