#!/usr/bin/env python3
"""Staleness audit + regeneration for the Fix Trading Loops mod.

  mod_sync.py check            audit the mod against the installed game files
  mod_sync.py regen [--write]  rebuild every top-level REPLACE: object from vanilla,
                               re-applying the merchant_maintenance_efficiency edit
                               (dry-run diff unless --write)

Set EU5_GAME to override the game dir (the one containing in_game/ and main_menu/).
"""
import difflib, glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.environ.get("EU5_GAME") or os.path.expanduser(
    "~/.local/share/Steam/steamapps/common/Europa Universalis V/game")
EFF = re.compile(r'^\s*(selling|export|import)_efficiency\s*=\s*(\S+)')
MERCH = "merchant_maintenance_efficiency"
# Hand-maintained REPLACE: objects regen must not touch (nested omen / deliberate edits).
SKIP_REGEN = {"hermes_god", "asian_trade_boom_modifier"}
TIERS = ["tiny", "small", "medium", "large", "huge"]
TIER_RE = re.compile(r'^(tiny|small|medium|large|huge)_(?:trade|selling|trade_sea|trade_land)_efficiency_(bonus|penalty)$')


def read(p):
    return open(p, encoding="utf-8-sig").read()


def strip_comment(l):
    return l.split("#", 1)[0]


def top_objects(text):
    """{name: (start, end)} char spans of column-0 `name = {` objects (prefix stripped)."""
    out = {}
    for m in re.finditer(r'^(?:(?:REPLACE|INJECT|TRY_INJECT|TRY_REPLACE|CREATE|REPLACE_OR_CREATE|INJECT_OR_CREATE):)?([^\s={}#]+)[ \t]*=[ \t]*\{', text, re.M):
        d, j = 0, m.end() - 1
        while j < len(text):
            c = text[j]
            if c == "#":
                j = text.find("\n", j)
                if j < 0: break
            elif c == "{": d += 1
            elif c == "}":
                d -= 1
                if d == 0: break
            j += 1
        out[m.group(1)] = (m.start(), j + 1)
    return out


def mod_files():
    return sorted(f for f in glob.glob(ROOT + "/**/*.txt", recursive=True) if "/tools/" not in f)


def rel(p):
    return os.path.relpath(p, ROOT)


def vanilla_dir_objects(reldir):
    """All top-level vanilla objects found under the same directory: {name: (file, text)}."""
    res = {}
    for f in sorted(glob.glob(os.path.join(GAME, reldir, "**/*.txt"), recursive=True)):
        t = read(f)
        for k, (s, e) in top_objects(t).items():
            res.setdefault(k, (f, t[s:e]))
    return res


def norm(text):
    return [l.strip() for l in (strip_comment(x) for x in text.splitlines())
            if l.strip() and MERCH not in l]


def merchant_for(tiers):
    """Largest-magnitude tier among a block's efficiency lines -> merchant value name."""
    best = max(tiers, key=lambda t: (TIERS.index(t[0]), t[1] == "bonus"))
    return f"{best[0]}_merchant_maintenance_efficiency_{best[1]}"


def add_merchant_lines(obj, report):
    """Insert one merchant line per block holding efficiency lines (after the last one)."""
    lines = obj.split("\n")
    stack, blocks = [], {}
    for i, l in enumerate(lines):
        code = strip_comment(l)
        m = EFF.match(code)
        if m:
            blk = stack[-1] if stack else -1
            blocks.setdefault(blk, []).append((i, m.group(2)))
        for c in code:
            if c == "{": stack.append(i)
            elif c == "}" and stack: stack.pop()
    for blk, items in sorted(blocks.items(), key=lambda kv: -kv[1][-1][0]):
        tiers = []
        for _, val in items:
            m = TIER_RE.match(val)
            if m: tiers.append((m.group(1), m.group(2)))
            else: report.append(f"unmapped value '{val}' (line {items[0][0]+1})")
        if not tiers: continue
        i = items[-1][0]
        indent = re.match(r'\s*', lines[i]).group(0)
        lines.insert(i + 1, f"{indent}{MERCH} = {merchant_for(tiers)}")
    return "\n".join(lines)


# ---------------------------------------------------------------- check
def check():
    problems = 0
    covered, van_all = set(), {}
    for f in mod_files():
        r = rel(f)
        if r.startswith((".metadata", "README")): continue
        t = read(f)
        reldir = os.path.dirname(r)
        base = os.path.basename(f)
        if not base.startswith("TE2_"):
            vf = os.path.join(GAME, r)
            if os.path.exists(vf):
                a, b = read(vf).splitlines(), t.splitlines()
                n = sum(1 for l in difflib.unified_diff(a, b, n=0, lineterm="") if l[:1] in "+-" and l[:3] not in ("+++", "---"))
                print(f"[full-file override] {r}: {n} differing lines vs vanilla")
            continue
        vobjs = vanilla_dir_objects(reldir)
        for k, (s, e) in top_objects(t).items():
            pre = re.match(r'(\w+):', t[s:e])
            kind = pre.group(1) if pre else "NEW"
            covered.add(k)
            if k not in vobjs:
                if kind in ("INJECT", "REPLACE"):
                    print(f"[missing target] {r}: {kind}:{k} not found in vanilla {reldir}"); problems += 1
                continue
            vtext = vobjs[k][1]
            has_eff = bool(re.search(r'\b(selling|export|import)_efficiency\s*=', vtext))
            if kind == "INJECT" and not has_eff:
                print(f"[stale compensation] {r}: INJECT:{k} - vanilla object has no selling/export/import_efficiency"); problems += 1
            if kind == "REPLACE":
                a = [l for l in norm(vtext)]
                b = [l for l in norm(t[s:e])]
                a[0] = b[0] = "HEAD"
                d = [l for l in difflib.unified_diff(a, b, n=0, lineterm="") if l[:1] in "+-" and l[:3] not in ("+++", "---")]
                if d:
                    print(f"[stale REPLACE] {r}: {k} differs from 1.x vanilla in {len(d)} lines")
                    for l in d[:4]: print("      ", l)
                    problems += 1
        # nested REPLACE: (e.g. omens) - compare by name against any vanilla occurrence
        for m in re.finditer(r'^[ \t]+REPLACE:([^\s={}]+)', t, re.M):
            print(f"[manual check] {r}: nested REPLACE:{m.group(1)} - verify by hand")
    # coverage: vanilla objects that grant efficiency but nothing in the mod touches
    uncovered = []
    for sub in ("in_game/common", "main_menu/common"):
        for f in glob.glob(os.path.join(GAME, sub, "**/*.txt"), recursive=True):
            if any(x in f for x in ("script_values", "game_concepts", "modifier_icons", "modifier_type_definitions")): continue
            t = read(f)
            for k, (s, e) in top_objects(t).items():
                if re.search(r'^\s*(selling|export|import)_efficiency\s*=', t[s:e], re.M) and k not in covered:
                    uncovered.append((os.path.relpath(f, GAME), k))
    for fpath, k in sorted(uncovered):
        print(f"[uncovered] {fpath}: {k}"); problems += 1
    print(f"\n{problems} problem(s)")
    return problems


# ---------------------------------------------------------------- regen
def regen(write):
    for f in mod_files():
        r = rel(f)
        if not os.path.basename(f).startswith("TE2_") or r.startswith("tools"): continue
        t = read(f)
        vobjs = vanilla_dir_objects(os.path.dirname(r))
        new, changed = t, False
        for k, (s, e) in sorted(top_objects(t).items(), key=lambda kv: -kv[1][0]):
            if not t[s:e].startswith("REPLACE:") or k in SKIP_REGEN: continue
            if k not in vobjs: print(f"skip {r}:{k} (no vanilla)"); continue
            rep = []
            body = add_merchant_lines(vobjs[k][1], rep)
            body = "REPLACE:" + body
            if rep: print(f"  !! {r}:{k}: " + "; ".join(rep))
            if body != t[s:e]:
                new = new[:s] + body + new[e:]; changed = True
                print(f"regen {r}:{k}")
        if changed and write:
            open(f, "w", encoding="utf-8").write(new)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "check": sys.exit(1 if check() else 0)
    elif cmd == "regen": regen("--write" in sys.argv)
    else: print(__doc__)
