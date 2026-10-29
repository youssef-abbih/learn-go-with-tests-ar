---
description: Translate one chapter of Learn Go with Tests into Arabic, in two phases (terminology approval, then translation and checks)
argument-hint: <chapter-file.md>
---

Translate the chapter `$ARGUMENTS` into Arabic, following every rule in
`CLAUDE.md`.

## Phase 1 — terminology (stop at the end of this phase)

1. Read `CLAUDE.md` and `glossary.md`. Read the English original with
   `git show arabic-version:$ARGUMENTS` (the working-tree file may already
   be partly Arabic).
2. List every technical term in the chapter's prose (not inside code) that
   is not in the glossary yet.
3. For each one, propose an Arabic term, add it to `glossary.md` with
   status `مقترح`, and give a one-line reason.
4. Also list the glossary terms this chapter uses that are still `مقترح`.
5. **Stop.** Show me both lists and wait. I will approve, change or reject
   terms by editing `glossary.md` or by telling you.

## Phase 2 — translation (only after I say to continue)

1. Re-read `glossary.md` (I may have changed it).
2. Write the translation over `$ARGUMENTS` in place. If the file is
   already partly or fully translated, keep the existing Arabic and fix it
   to follow the rules instead of retranslating from scratch.
3. Run `python3 tools/check_translation.py $ARGUMENTS` and fix every error.
   Fix every warning you can; keep the rest for the report.
4. Make sure the chapter's title in `SUMMARY.md` is in Arabic.
5. Report, briefly:
   - warnings left and why,
   - `مقترح` terms still used,
   - passages you were unsure about, with line numbers in `$ARGUMENTS`.
