"""Check every relative Markdown link and #anchor in the repository. Usage: python scripts/check_markdown_links.py [ROOT]. Exit 1 on problems."""
import re, sys, pathlib, urllib.parse
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
skip = {".git", "node_modules", "webdist", "dist", ".venv", "e2e-artifacts"}
def slug(h):
    h = h.strip().lower()
    h = re.sub(r"[^\w\- ]", "", h)   # GitHub-style
    return h.replace(" ", "-")
def anchors(p):
    out = set()
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^#{1,6}\s+(.*)", line)
        if m: out.add(slug(re.sub(r"[`*_]", "", m.group(1))))
    return out
bad = []
files = [p for p in root.rglob("*.md") if not (set(p.relative_to(root).parts) & skip)]
for md in files:
    text = md.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r"\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", text):
        target = m.group(1)
        if re.match(r"^(https?:|mailto:)", target): continue
        path, _, frag = target.partition("#")
        path = urllib.parse.unquote(path)
        dest = (md.parent / path).resolve() if path else md.resolve()
        if path and not dest.exists():
            bad.append(f"{md.relative_to(root)}: missing {target}"); continue
        if frag and dest.suffix == ".md" and dest.exists() and frag not in anchors(dest):
            bad.append(f"{md.relative_to(root)}: no anchor #{frag} in {dest.relative_to(root)}")
print(f"{len(files)} markdown files checked; {len(bad)} problems")
print("\n".join(bad))
sys.exit(1 if bad else 0)
