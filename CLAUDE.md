# Arabic translation of Learn Go with Tests

This repository is a fork of `quii/learn-go-with-tests`. The goal is a
complete, consistent Arabic translation published as a GitBook site.

## Layout

- The translation is done **in place on `main`**: each Arabic file replaces
  its English original at the same path (for example `hello-world.md`).
- Branch `arabic-version`: the untouched English base this translation
  started from. **Never modify it.** It is the reference for every check:
  `git show arabic-version:<file>` gives the English original of `<file>`.
- `SUMMARY.md`: table of contents (GitBook), translated.
- `glossary.md`: the single source of truth for terminology.
- `tools/check_translation.py`: structural and terminology checker.
- Text direction is handled by GitBook settings.
  **Never add manual direction markup** (HTML `dir` attributes, `<div>`
  wrappers, Unicode direction marks) to chapters. If an existing chapter
  has some, remove it.

## Hard rules

1. **Code is never touched.** Fenced code blocks are copied byte for byte,
   including the comments inside them. Do not translate code comments.
2. **Identifiers stay English and in inline code.** Every function, type,
   variable, package, keyword, command, flag and file name is written in
   backticks and never translated. If the original mentions one without
   backticks, add them in the translation.
3. **Markdown structure is preserved.** Same headings (count and level),
   same link targets, same images, same lists and tables.
4. **Terminology comes only from `glossary.md`.**
   - Status `معتمد`: use the Arabic term exactly.
   - Status `مقترح`: you may use it, but list it in your report.
   - Status `يبقى بالإنجليزية`: keep the English term, in inline code.
   - A term not in the glossary: never invent it silently. Add a row with
     status `مقترح` and list it in your report.
   - First occurrence of a glossary term in a chapter: Arabic term followed
     by the English in parentheses. After that: Arabic only.
5. **Bidirectional text rules** (these keep the RTL rendering correct):
   - No paragraph, list item or heading may start with a Latin word or
     with inline code, and none may end with a Latin word followed by
     punctuation. Rephrase the Arabic sentence so the Latin part sits in
     the middle.
   - Use Arabic punctuation next to Arabic text: `،` `؛` `؟`.
   - Use Western digits (0-9), consistent with code and program output.
6. **Style.** Modern Standard Arabic, clear technical prose, not literal
   word-for-word translation. Keep the author's direct, informal tone.
   Do not add or drop content. A translator's note is allowed only as a
   blockquote starting with `ملاحظة المترجم:`.
7. **Never commit, push or open a pull request unless asked.**

## Checks

- Structure and terminology for one chapter:
  `python3 tools/check_translation.py <chapter>.md`
  Errors must be zero. Warnings must be fixed or explained in the report.
  A warning "inline code added" is expected when rule 2 added backticks.

## Updating after upstream changes

1. `git fetch upstream` (upstream = `quii/learn-go-with-tests`).
2. See what changed in the English text since the base:
   `git diff arabic-version upstream/main -- <chapter>.md`
3. `git merge upstream/main` into `main`. For every conflicted chapter,
   keep the Arabic side, then translate the English changes from step 2
   into it. New chapters arrive in English and are translated as usual.
4. When every changed chapter is done, move the base forward:
   `git branch -f arabic-version upstream/main`
