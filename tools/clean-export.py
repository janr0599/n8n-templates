#!/usr/bin/env python3
"""Turn an n8n export into a publishable template.

n8n never exports secrets, but it does export credential *references* (id and
display name), and it exports everything you wrote: node names, notes, sticky
text, URLs, record ids, addresses. This strips the references and refuses to
write the file if anything that looks identifying is still in it.

Usage:
    python3 tools/clean-export.py raw-export.json 04-.../workflow.json
    python3 tools/clean-export.py raw.json out.json --allow example-public.com
"""
import argparse, json, pathlib, re, sys

DROP_WORKFLOW_KEYS = {"id", "versionId", "meta", "tags", "active", "isArchived",
                      "createdAt", "updatedAt", "triggerCount", "shared",
                      "parentFolderId", "scopes", "activeVersion", "activeVersionId"}

# Anything matching these must be reviewed before the file can be published.
RISK = {
    "credential reference": r'"credentials"\s*:',
    "email address":        r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
    "Airtable base/table":  r'\b(?:app|tbl|fld|rec)[A-Za-z0-9]{14}\b',
    "private hostname":     r'https?://(?!YOUR_)[A-Za-z0-9.-]*\.(?:local|internal)[A-Za-z0-9.-]*',
    # Real ids mix case and digits; n8n's own camelCase parameter names do not.
    "long opaque id":       r'\b(?=[A-Za-z0-9]*[0-9])(?=[A-Za-z0-9]*[a-z])(?=[A-Za-z0-9]*[A-Z])[A-Za-z0-9]{16,}\b',
}
# Words that should never appear in a public template, whatever the context:
# your own company, your clients, their trading names. The list lives outside the
# repo, because a public blocklist publishes exactly what it is meant to protect.
BLOCKLIST = pathlib.Path(__file__).with_name("blocklist.local.txt")


def load_never():
    if not BLOCKLIST.exists():
        sys.exit(
            "missing %s\n\n"
            "This file holds the names that must never reach a public template.\n"
            "It is gitignored on purpose. Create it from the example:\n\n"
            "    cp %s %s\n\n"
            "then put one name per line, lowercase." % (
                BLOCKLIST, BLOCKLIST.with_name("blocklist.example.txt"), BLOCKLIST)
        )
    words = []
    for line in BLOCKLIST.read_text().splitlines():
        line = line.split("#", 1)[0].strip().lower()
        if line:
            words.append(line)
    if not words:
        sys.exit("%s is empty. Refusing to scan without a blocklist." % BLOCKLIST)
    return words


def clean(wf):
    for key in DROP_WORKFLOW_KEYS:
        wf.pop(key, None)
    stripped = []
    for node in wf.get("nodes", []):
        if node.pop("credentials", None) is not None:
            stripped.append(node.get("name", "?"))
        for key in ("webhookId", "credentials"):
            node.pop(key, None)
    wf.setdefault("settings", {"executionOrder": "v1"})
    wf.setdefault("pinData", {})
    return stripped


def scan(blob, allow):
    findings = []
    for word in load_never():
        if word in blob.lower():
            findings.append(("banned word", word))
    for label, pattern in RISK.items():
        for hit in sorted(set(re.findall(pattern, blob))):
            if any(a.lower() in hit.lower() for a in allow):
                continue
            if label == "long opaque id" and hit.startswith("YOUR_"):
                continue
            findings.append((label, hit))
    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dest")
    ap.add_argument("--allow", nargs="*", default=[], help="strings that are safe to keep")
    ap.add_argument("--force", action="store_true", help="write even with findings")
    args = ap.parse_args()

    wf = json.load(open(args.src))
    stripped = clean(wf)
    blob = json.dumps(wf, ensure_ascii=False)
    findings = scan(blob, args.allow)

    if stripped:
        print(f"stripped credentials from {len(stripped)} node(s): {', '.join(stripped)}")
    if findings:
        print(f"\n{len(findings)} thing(s) to review before publishing:")
        for label, hit in findings:
            print(f"  {label:20} {hit[:70]}")
        if not args.force:
            print("\nNot written. Fix them, or re-run with --allow / --force if they are safe.")
            return 1

    json.dump(wf, open(args.dest, "w"), indent=2, ensure_ascii=False)
    open(args.dest, "a").write("\n")
    print(f"\nwrote {args.dest}  ({len(wf.get('nodes', []))} nodes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
