#!/usr/bin/env python3
"""kb - knowledge-base lifecycle engine (stdlib only).

Usage:
  python kb.py check   [--root DIR] [--quiet]
  python kb.py index   [--root DIR]
  python kb.py status  <path> [--root DIR]
  python kb.py set-status <path> <status> [--root DIR] [--force]
  python kb.py archive <path> [--superseded-by P] [--reason R] [--root DIR]

The rules live in schema.yaml next to this script (or at the path the workspace's
docs/kb.yaml points to). A workspace config carries paths only, never rules.
"""

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SCHEMA = DEFAULT_SKILL_DIR / "schema.yaml"

FALLBACK_SCHEMA = {
    "schema_version": 1,
    "statuses": {s: {} for s in ["draft", "active", "final", "archived"]},
    "types": {
        "framework": ["draft", "active", "archived"],
        "specs": ["draft", "active", "archived"],
        "knowledge": ["draft", "active", "archived"],
        "ops": ["draft", "active", "archived"],
        "plans": ["draft", "active", "final", "archived"],
        "reviews": ["active", "final", "archived"],
        "decisions": ["active", "archived"],
        "archive": ["archived"],
    },
    "defaults": {"framework": "active", "specs": "draft", "knowledge": "active",
                 "ops": "active", "plans": "active", "reviews": "final",
                 "decisions": "active", "archive": "archived"},
    "archive_reasons": ["superseded", "absorbed", "historical", "withdrawn", "obsolete", "completed"],
    "fields": {"decisions": ["Topic"], "specs": ["Decision"], "plans": ["Spec"]},
    "transitions": {"draft": ["active", "archived"], "active": ["final", "archived", "draft"],
                    "final": ["archived"], "archived": ["draft", "active"]},
    "index_columns": {"active": ["path", "type", "status"],
                      "archive": ["path", "status", "superseded_by", "sha256", "reason"]},
    "index_markers": {
        "active_start": "<!-- kb:active:start -->",
        "active_end": "<!-- kb:active:end -->",
        "archive_start": "<!-- kb:archive:start -->",
        "archive_end": "<!-- kb:archive:end -->",
    },
}


HOOK_TEMPLATE = """#!/bin/sh
# installed by kb - validates docs lifecycle before commit
if [ -z "$KB" ]; then KB="$HOME/.dsh/skills/knowledge-base/scripts/kb.py"; fi
if [ ! -f "$KB" ]; then
  echo "kb: skill not found at $KB; docs check skipped"
  exit 0
fi
python "$KB" check
"""



# ---------------------------------------------------------------- decisions
ADR_ID_RE = re.compile(r"^ADR-([0-9]{4}[a-z]?)$")
ADR_FILE_RE = re.compile(r"^([0-9]{4}[a-z]?)-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
TOPIC_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FIELD_LINE_RE = re.compile(r"^\*\*([A-Za-z]+):\*\*\s*(.*?)\s*$")
N_A_RE = re.compile(r"^N/A\s*(?:—|-|:)\s*(\S.*)$")


def decisions_enabled(cfg):
    return "decisions" in (cfg.get("types") or {})


def adr_id_of(relpath):
    m = ADR_FILE_RE.match(Path(relpath).name)
    return "ADR-" + m.group(1) if m else None


def archive_type_of(relpath, archive_dir):
    prefix = archive_dir.rstrip("/") + "/"
    if not relpath.startswith(prefix):
        return ""
    rest = relpath[len(prefix):]
    return rest.split("/", 1)[0] if "/" in rest else ""


def read_fields(path, names):
    """Return {field name: [values in file order]} for '**Name:** value' lines."""
    out = {n: [] for n in names}
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return out
    for line in text.splitlines():
        m = FIELD_LINE_RE.match(line)
        if m and m.group(1) in out:
            out[m.group(1)].append(m.group(2))
    return out


def na_reason(value):
    m = N_A_RE.match(value.strip())
    return m.group(1).strip() if m else None


def split_list(value):
    return [part.strip() for part in value.split(",")]


def build_adr_id_map(root, cfg, schema, active_map, archive_map):
    """Map ADR id -> {path, status, superseded_by, tree}; report bad names and duplicate ids."""
    errors = []
    id_map = {}
    for f, row in active_map.items():
        if row[1] != "decisions":
            continue
        aid = adr_id_of(f)
        if not aid:
            errors.append("bad ADR filename (want NNNN-slug.md): " + f)
            continue
        if aid in id_map:
            errors.append("duplicate ADR id " + aid + ": " + id_map[aid]["path"] + ", " + f)
            continue
        id_map[aid] = {"path": f, "status": row[2], "superseded_by": "", "tree": "active"}
    for f, row in archive_map.items():
        if archive_type_of(f, cfg["archive"]) != "decisions":
            continue
        aid = adr_id_of(f)
        if not aid:
            errors.append("bad ADR filename (want NNNN-slug.md): " + f)
            continue
        if aid in id_map:
            errors.append("duplicate ADR id " + aid + ": " + id_map[aid]["path"] + ", " + f)
            continue
        id_map[aid] = {"path": f, "status": "archived",
                       "superseded_by": row[2] if len(row) > 2 else "", "tree": "archive"}
    return errors, id_map


def check_binding(root, cfg, f, name, value, id_map, active_map):
    errors = []
    value = value.strip()
    if value.startswith("N/A"):
        if not na_reason(value):
            errors.append(name + ": N/A requires a reason in " + f)
        return errors
    if name == "Decision":
        seen = set()
        for aid in split_list(value):
            if not ADR_ID_RE.match(aid):
                errors.append("invalid ADR id '" + aid + "' in " + f)
                continue
            if aid in seen:
                errors.append("duplicate ADR in Decision: " + aid + " in " + f)
                continue
            seen.add(aid)
            ent = id_map.get(aid)
            if not ent:
                errors.append("unknown ADR " + aid + " in " + f)
            elif ent["status"] != "active":
                msg = f + ": Decision " + aid + " is archived"
                if ent.get("superseded_by"):
                    msg += " (successor " + ent["superseded_by"] + ")"
                errors.append(msg)
    elif name == "Spec":
        p = value
        if "\\" in p or not p.startswith("docs/") or not p.endswith(".md"):
            errors.append("Spec must be a docs/... .md path in " + f)
            return errors
        if not (root / p).is_file():
            errors.append("unknown spec " + p + " in " + f)
            return errors
        row = active_map.get(p)
        if row is None:
            errors.append("spec " + p + " is not active in " + f)
        elif row[1] != "specs":
            errors.append("spec " + p + " is not a specs doc in " + f)
        elif row[2] != "active":
            errors.append("spec " + p + " is not active (status " + row[2] + ") in " + f)
    return errors


def check_decisions(root, cfg, schema, active_map, archive_map):
    fields_cfg = schema.get("fields") or {}
    errors, id_map = build_adr_id_map(root, cfg, schema, active_map, archive_map)
    topic_field = (fields_cfg.get("decisions") or ["Topic"])[0]

    topics = {}
    for f, row in active_map.items():
        if row[1] != "decisions":
            continue
        got = read_fields(root / f, [topic_field])[topic_field]
        if len(got) > 1:
            errors.append("duplicate field " + topic_field + " in " + f)
            continue
        if not got or not got[0].strip():
            errors.append("missing " + topic_field + " in " + f)
            continue
        seen = set()
        bad = False
        for token in split_list(got[0]):
            if not token or not TOPIC_RE.match(token):
                errors.append("invalid topic '" + token + "' in " + f)
                bad = True
            elif token in seen:
                errors.append("invalid topic '" + token + "' (duplicate) in " + f)
                bad = True
            else:
                seen.add(token)
        if bad:
            continue
        for token in seen:
            topics.setdefault(token, []).append(f)
    for token, paths in topics.items():
        if len(paths) > 1:
            errors.append("topic '" + token + "' has " + str(len(paths)) + " active ADRs: " + ", ".join(paths))

    for doc_type, names in fields_cfg.items():
        if doc_type == "decisions":
            continue
        for f, row in active_map.items():
            if row[1] != doc_type:
                continue
            values = read_fields(root / f, names)
            for name in names:
                got = values[name]
                if len(got) > 1:
                    errors.append("duplicate field " + name + " in " + f)
                    continue
                if not got:
                    errors.append("missing " + name + " in " + f)
                    continue
                errors.extend(check_binding(root, cfg, f, name, got[0], id_map, active_map))
    return errors, id_map

# ---------------------------------------------------------------- tiny yaml
def _scalar(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
        return v[1:-1]
    if v.lower() in ("yes", "true"):
        return True
    if v.lower() in ("no", "false"):
        return False
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return v


def _inline_list(v):
    inner = v.strip()[1:-1].strip()
    if not inner:
        return []
    return [_scalar(x) for x in inner.split(",")]


def _inline_map(v):
    inner = v.strip()[1:-1].strip()
    out = {}
    if not inner:
        return out
    for part in inner.split(","):
        k, _, val = part.partition(":")
        out[k.strip()] = _scalar(val)
    return out


def load_simple_yaml(path):
    """Parse the YAML subset used by schema.yaml / kb.yaml (maps, inline lists, comments)."""
    lines = []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.split(" #")[0].rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        lines.append((len(line) - len(line.lstrip()), line.strip()))

    def parse_block(i, indent):
        node = {}
        while i < len(lines):
            ind, text = lines[i]
            if ind < indent:
                break
            if ind > indent:
                raise ValueError("unexpected indent at line: " + text)
            if ":" not in text:
                raise ValueError("not a key: " + text)
            key, rest = text.split(":", 1)
            key = key.strip()
            rest = rest.strip()
            if rest.startswith("[") and rest.endswith("]"):
                node[key] = _inline_list(rest)
                i += 1
            elif rest.startswith("{") and rest.endswith("}"):
                node[key] = _inline_map(rest)
                i += 1
            elif rest == "":
                if i + 1 < len(lines) and lines[i + 1][0] > ind:
                    child, i = parse_block(i + 1, lines[i + 1][0])
                    node[key] = child
                else:
                    node[key] = ""
                    i += 1
            else:
                node[key] = _scalar(rest)
                i += 1
        return node, i

    data, _ = parse_block(0, lines[0][0] if lines else 0)
    return data


# ---------------------------------------------------------------- config
def find_root(start):
    p = Path(start).resolve()
    while True:
        if (p / "docs" / "kb.yaml").is_file():
            return p
        if p.parent == p:
            return None
        p = p.parent


def load_config(root):
    cfg = load_simple_yaml(root / "docs" / "kb.yaml")
    cfg.setdefault("types", {
        "framework": "docs/framework", "specs": "docs/specs", "plans": "docs/plans",
        "knowledge": "docs/knowledge", "reviews": "docs/reviews", "ops": "docs/ops",
    })
    if not isinstance(cfg.get("types"), dict):
        raise SystemExit("kb: docs/kb.yaml 'types' must be a block mapping (one 'name: path' per line)")
    cfg.setdefault("archive", "docs/archive")
    cfg.setdefault("index", "docs/INDEX.md")
    cfg.setdefault("archive_index", "docs/archive/INDEX.md")
    cfg.setdefault("root_files", [])
    return cfg


def load_schema(cfg, root):
    candidates = []
    if cfg.get("schema"):
        candidates.append(Path(cfg["schema"]))
    if os.environ.get("KB_SCHEMA"):
        candidates.append(Path(os.environ["KB_SCHEMA"]))
    candidates.append(DEFAULT_SCHEMA)
    candidates.append(root / "docs" / "kb-schema.yaml")
    for c in candidates:
        if Path(c).is_file():
            return load_simple_yaml(c)
    return dict(FALLBACK_SCHEMA)


# ---------------------------------------------------------------- index io
def sha256_file(p):
    h = hashlib.sha256()
    h.update(Path(p).read_bytes())
    return h.hexdigest()


def split_row(line):
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return cells


def read_table(path, markers, columns):
    if not Path(path).is_file():
        return []
    text = Path(path).read_text(encoding="utf-8")
    start, end = markers
    if start in text and end in text:
        block = text.split(start, 1)[1].split(end, 1)[0]
    else:
        block = ""
    rows = []
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = split_row(line)
        if not cells or cells[0] in ("", "path") or set(cells[0]) <= set("-: "):
            continue
        rows.append(cells)
    return rows


def write_table(path, markers, columns, rows):
    start, end = markers
    p = Path(path)
    text = p.read_text(encoding="utf-8") if p.is_file() else start + "\n" + end + "\n"
    if start not in text or end not in text:
        text = text.rstrip() + "\n\n" + start + "\n" + end + "\n"
    head = text.split(start, 1)[0]
    tail = text.split(end, 1)[1]
    out = [start, "", "| " + " | ".join(columns) + " |",
           "|" + "|".join(["---"] * len(columns)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(c) for c in row) + " |")
    out += ["", end]
    p.write_text(head + "\n".join(out) + tail, encoding="utf-8")


def markers_for(schema, which):
    m = schema.get("index_markers", FALLBACK_SCHEMA["index_markers"])
    return (m[which + "_start"], m[which + "_end"])


# ---------------------------------------------------------------- checks
LINK_BARE = re.compile(r"docs/[A-Za-z0-9_.\-/]+\.md")
LINK_MD = re.compile(r"\]\(([^)\s]+)\)")


def iter_md(root, rel_dir, exclude=None):
    base = root / rel_dir
    if not base.is_dir():
        return []
    out = []
    for p in sorted(base.rglob("*.md")):
        rp = p.relative_to(root).as_posix()
        if exclude and rp == exclude:
            continue
        out.append(rp)
    return out


def cmd_check(args):
    root = resolve_root(args.root)
    if root is None:
        print("kb: no docs/kb.yaml found (run from a workspace root or pass --root)")
        return 2
    cfg = load_config(root)
    schema = load_schema(cfg, root)
    types = cfg["types"]
    archive_dir = cfg["archive"]
    errors = []

    active_rows = read_table(root / cfg["index"], markers_for(schema, "active"), ["path", "type", "status"])
    archive_rows = read_table(root / cfg["archive_index"], markers_for(schema, "archive"),
                              schema["index_columns"]["archive"])
    active_map = {r[0]: r for r in active_rows}
    archive_map = {r[0]: r for r in archive_rows}

    # 1. files in active tree must be listed, with a valid status for their type
    active_files = []
    for t, rel in types.items():
        active_files += iter_md(root, rel)
    for f in active_files:
        if f not in active_map:
            errors.append("missing from active index: " + f)
            continue
        t = f.split("/")[1]
        st = active_map[f][2] if len(active_map[f]) > 2 else ""
        allowed = schema["types"].get(t, [])
        if st not in allowed:
            errors.append("invalid status '" + st + "' for " + f + " (allowed: " + ", ".join(allowed) + ")")
        if st == "archived":
            errors.append("archived status on an active path: " + f)

    # 2. index rows must point at real files of the right type
    for f, r in active_map.items():
        if not (root / f).is_file():
            errors.append("index row points at a missing file: " + f)
        parts = f.split("/")
        if len(parts) < 3 or parts[0] != "docs" or parts[1] not in types:
            errors.append("path outside a configured type dir: " + f)
        elif f.split("/")[1] != (r[1] if len(r) > 1 else ""):
            errors.append("type column mismatch for " + f)

    # 3. archive
    archive_files = iter_md(root, archive_dir, exclude=cfg["archive_index"])
    for f in archive_files:
        if f not in archive_map:
            errors.append("missing from archive index: " + f)
            continue
        row = archive_map[f]
        if len(row) > 2 and row[1] != "archived":
            errors.append("archive row status must be archived: " + f)
        recorded = row[3] if len(row) > 3 else ""
        actual = sha256_file(root / f)
        if recorded != actual:
            errors.append("frozen archive changed (sha256 mismatch): " + f)
    for f in archive_map:
        if not (root / f).is_file():
            errors.append("archive row points at a missing file: " + f)
    for f in active_map:
        if f.startswith(archive_dir + "/"):
            errors.append("archived path also listed as active: " + f)

    # 4. decisions protocol (opt-in) and superseded_by targets
    id_map = {}
    if decisions_enabled(cfg):
        derrors, id_map = check_decisions(root, cfg, schema, active_map, archive_map)
        errors.extend(derrors)
    for f, row in archive_map.items():
        target = row[2] if len(row) > 2 else ""
        if not target:
            continue
        if ADR_ID_RE.match(target):
            if target not in id_map:
                errors.append("superseded_by target missing for " + f + ": " + target)
        elif not (root / target).is_file() and not (root / target).is_dir():
            errors.append("superseded_by target missing for " + f + ": " + target)

    # 5. links resolve
    check_files = list(active_files)
    for rf in cfg.get("root_files", []) or []:
        if (root / rf).is_file():
            check_files.append(rf)
    for f in check_files:
        text = (root / f).read_text(encoding="utf-8", errors="replace")
        for hit in set(LINK_BARE.findall(text)):
            if not (root / hit).is_file():
                errors.append("broken link in " + f + ": " + hit)
        for target in LINK_MD.findall(text):
            if re.match(r"^[a-z]+:|^#|^<", target):
                continue
            t = target.split("#")[0]
            if not t:
                continue
            resolved = (Path(f).parent / t)
            if not (root / resolved).exists():
                errors.append("broken relative link in " + f + ": " + target)

    if errors:
        print("kb check: FAIL (" + str(len(errors)) + " problem(s))")
        for e in errors:
            print("  - " + e)
        return 1
    print("kb check: OK (" + str(len(active_files)) + " active, " + str(len(archive_files)) + " archived)")
    return 0


# ---------------------------------------------------------------- index
def cmd_index(args):
    root = resolve_root(args.root)
    if root is None:
        print("kb: no docs/kb.yaml found")
        return 2
    cfg = load_config(root)
    schema = load_schema(cfg, root)
    types = cfg["types"]

    old = {r[0]: r for r in read_table(root / cfg["index"], markers_for(schema, "active"),
                                       schema["index_columns"]["active"])}
    rows = []
    new_files = []
    for t, rel in types.items():
        for f in iter_md(root, rel):
            prev = old.get(f)
            if prev and len(prev) > 2 and prev[2] in schema["types"].get(t, []):
                st = prev[2]
            else:
                st = schema["defaults"].get(t, "active")
                if f not in old:
                    new_files.append(f)
            rows.append([f, t, st])
    write_table(root / cfg["index"], markers_for(schema, "active"),
                schema["index_columns"]["active"], rows)

    aold = {r[0]: r for r in read_table(root / cfg["archive_index"],
                                        markers_for(schema, "archive"),
                                        schema["index_columns"]["archive"])}
    arows = []
    for f in iter_md(root, cfg["archive"], exclude=cfg["archive_index"]):
        prev = aold.get(f, [f, "archived", "", "", ""])
        sup = prev[2] if len(prev) > 2 else ""
        reason = prev[4] if len(prev) > 4 else ""
        arows.append([f, "archived", sup, sha256_file(root / f), reason])
    write_table(root / cfg["archive_index"], markers_for(schema, "archive"),
                schema["index_columns"]["archive"], arows)

    print("kb index: " + str(len(rows)) + " active, " + str(len(arows)) + " archived")
    for f in new_files:
        print("  new (defaults applied): " + f)
    return 0


# ---------------------------------------------------------------- helpers
def resolve_root(arg):
    if arg:
        return Path(arg).resolve()
    return find_root(os.getcwd())


def all_rows(root, cfg, schema):
    return (read_table(root / cfg["index"], markers_for(schema, "active"), ["path", "type", "status"]),
            read_table(root / cfg["archive_index"], markers_for(schema, "archive"),
                       schema["index_columns"]["archive"]))


def rel(path, root):
    p = Path(path)
    try:
        return p.resolve().relative_to(root).as_posix()
    except ValueError:
        return p.as_posix()


def cmd_status(args):
    root = resolve_root(args.root)
    cfg = load_config(root)
    schema = load_schema(cfg, root)
    target = rel(args.path, root)
    act, arc = all_rows(root, cfg, schema)
    for r in act:
        if r[0] == target:
            print(target + ": " + r[2] + " (" + r[1] + ")")
            return 0
    for r in arc:
        if r[0] == target:
            print(target + ": archived" + (" -> " + r[2] if len(r) > 2 and r[2] else ""))
            return 0
    print("kb: not in any index: " + target)
    return 1


def cmd_set_status(args):
    root = resolve_root(args.root)
    cfg = load_config(root)
    schema = load_schema(cfg, root)
    target = rel(args.path, root)
    if args.status not in schema["statuses"]:
        print("kb: unknown status " + args.status)
        return 2
    act, arc = all_rows(root, cfg, schema)
    for r in act:
        if r[0] != target:
            continue
        t, cur = r[1], r[2]
        if not args.force and args.status not in schema["transitions"].get(cur, []):
            print("kb: illegal transition " + cur + " -> " + args.status + " (use --force to override)")
            return 1
        if args.status not in schema["types"].get(t, []):
            print("kb: status " + args.status + " not allowed for type " + t)
            return 1
        if args.status == "archived":
            print("kb: use 'kb archive' to move a file into the archive tree")
            return 1
        r[2] = args.status
        write_table(root / cfg["index"], markers_for(schema, "active"),
                    schema["index_columns"]["active"], act)
        print("kb: " + target + " -> " + args.status)
        return 0
    print("kb: not in the active index: " + target)
    return 1


def cmd_archive(args):
    root = resolve_root(args.root)
    cfg = load_config(root)
    schema = load_schema(cfg, root)
    src = root / rel(args.path, root)
    if not src.is_file():
        print("kb: file not found: " + str(src))
        return 2
    superseded_by = args.superseded_by
    if superseded_by and ADR_ID_RE.match(superseded_by):
        act, arc = all_rows(root, cfg, schema)
        _, id_map = build_adr_id_map(root, cfg, schema,
                                     {r[0]: r for r in act}, {r[0]: r for r in arc})
        ent = id_map.get(superseded_by)
        if not ent or ent["status"] != "active":
            print("kb: superseded_by must be an active ADR: " + superseded_by)
            return 2
    elif superseded_by and not (root / superseded_by).exists():
        print("kb: superseded_by target does not exist: " + superseded_by)
        return 2
    rp = src.relative_to(root).as_posix()
    parts = rp.split("/")
    t = parts[1] if len(parts) > 2 else "misc"
    dest = root / cfg["archive"] / t / src.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    tracked = subprocess.run(["git", "-C", str(root), "ls-files", "--error-unmatch", rp],
                             capture_output=True, text=True, encoding="utf-8", errors="replace")
    if tracked.returncode == 0:
        subprocess.run(["git", "-C", str(root), "mv", rp, dest.relative_to(root).as_posix()], check=True)
    else:
        shutil.move(str(src), str(dest))
    cmd_index(argparse.Namespace(root=str(root)))
    arc_path = dest.relative_to(root).as_posix()
    rows = read_table(root / cfg["archive_index"], markers_for(schema, "archive"),
                      schema["index_columns"]["archive"])
    for r in rows:
        if r[0] == arc_path:
            r[2] = superseded_by or ""
            r[4] = args.reason or ""
    write_table(root / cfg["archive_index"], markers_for(schema, "archive"),
                schema["index_columns"]["archive"], rows)
    print("kb: archived " + rp + " -> " + arc_path)
    return 0


# ---------------------------------------------------------------- refs
def cmd_refs(args):
    root = resolve_root(args.root)
    if root is None:
        print("kb: no docs/kb.yaml found (run from a workspace root or pass --root)")
        return 2
    cfg = load_config(root)
    schema = load_schema(cfg, root)
    if not decisions_enabled(cfg):
        print("kb: decisions type is not configured in docs/kb.yaml")
        return 2
    aid = args.adr_id.strip()
    if not ADR_ID_RE.match(aid):
        print("kb: bad ADR id: " + aid)
        return 2
    active_rows, archive_rows = all_rows(root, cfg, schema)
    active_map = {r[0]: r for r in active_rows}
    archive_map = {r[0]: r for r in archive_rows}
    _, id_map = build_adr_id_map(root, cfg, schema, active_map, archive_map)
    if aid not in id_map:
        print("kb: unknown ADR " + aid)
        return 2
    names = sorted({n for ns in (schema.get("fields") or {}).values() for n in ns})
    hits = []
    for f, row in active_map.items():
        for name, values in read_fields(root / f, names).items():
            if name != "Decision":
                continue
            for value in values:
                if value.strip().startswith("N/A"):
                    continue
                if aid in split_list(value):
                    hits.append((f, row[1], row[2]))
                    break
    print("kb refs " + aid + ": " + str(len(hits)) + " binding(s)")
    for f, t, st in hits:
        print("  " + f + " (" + t + ", " + st + ")")
    return 0


# ---------------------------------------------------------------- hook
def cmd_hook(args):
    root = resolve_root(args.root)
    if root is None:
        print("kb: no docs/kb.yaml found")
        return 2
    probe = subprocess.run(["git", "-C", str(root), "rev-parse", "--git-path", "hooks/pre-commit"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
    if probe.returncode != 0 or not probe.stdout:
        print("kb: not a git repository: " + str(root))
        return 2
    hook = Path(probe.stdout.strip())
    if not hook.is_absolute():
        hook = root / hook
    if args.remove:
        if hook.exists():
            hook.unlink()
            print("kb: removed " + str(hook))
        else:
            print("kb: no hook to remove")
        return 0
    hook.parent.mkdir(parents=True, exist_ok=True)
    if hook.exists():
        text = hook.read_text(encoding="utf-8", errors="replace")
        if "installed by kb" not in text:
            print("kb: refusing to overwrite an existing pre-commit hook; merge it manually")
            return 1
    hook.write_text(HOOK_TEMPLATE, encoding="utf-8", newline="\n")
    try:
        hook.chmod(0o755)
    except OSError:
        pass
    print("kb: installed hook " + str(hook))
    return 0


# ---------------------------------------------------------------- cli
def main(argv=None):
    ap = argparse.ArgumentParser(prog="kb")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("check"); p.add_argument("--root"); p.set_defaults(fn=cmd_check)
    p = sub.add_parser("index"); p.add_argument("--root"); p.set_defaults(fn=cmd_index)
    p = sub.add_parser("status"); p.add_argument("path"); p.add_argument("--root"); p.set_defaults(fn=cmd_status)
    p = sub.add_parser("set-status"); p.add_argument("path"); p.add_argument("status")
    p.add_argument("--root"); p.add_argument("--force", action="store_true"); p.set_defaults(fn=cmd_set_status)
    p = sub.add_parser("hook"); p.add_argument("--root")
    p.add_argument("--install", action="store_true")
    p.add_argument("--remove", action="store_true"); p.set_defaults(fn=cmd_hook)
    p = sub.add_parser("refs"); p.add_argument("adr_id"); p.add_argument("--root"); p.set_defaults(fn=cmd_refs)
    p = sub.add_parser("archive"); p.add_argument("path")
    p.add_argument("--superseded-by", dest="superseded_by"); p.add_argument("--reason")
    p.add_argument("--root"); p.set_defaults(fn=cmd_archive)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
