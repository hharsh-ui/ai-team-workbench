# Lessons Learned

The team's learning ledger. Search it before debugging or doing anything unfamiliar; add a lesson at the top
after fixing a problem or being corrected.

Each lesson has a **Status**: FIXED (fixed and verified), WORKAROUND (cause outside our control; follow the steps),
RULE (a way of working to follow from now on), NOT A BUG, OBSOLETE, or OPEN (not solved yet).

---

## [2026-10-25] Text extracted from a PDF was garbage although the pages looked fine

- **Status:** RULE
- **Symptom:** Text, tables and numbers extracted from a PDF were nonsense, while the page images were perfect.
- **Cause:** The PDF's fonts carry no character mapping (common after re-exporting through a printer driver or converter), so its text layer cannot be decoded.
- **Rule:** Check the Text column of the source pack's `INDEX.md`. For `unreadable` or `none` pages, transcribe from the page image (or OCR with approval), check twice, mark the transcript checked, and never use numbers from the broken text.

## [2026-10-25] Numbers in an AI-written summary did not match the source document

- **Status:** RULE
- **Symptom:** A summary generated from a PDF contained rounded, reformatted or invented numbers.
- **Cause:** The model paraphrased instead of copying, and did arithmetic in its head.
- **Rule:** Build a source pack, copy numbers exactly as printed, calculate only with code, and run `source_check_numbers` on every generated document before handing it over.

## [2026-10-25] PowerShell 5.1 shows red NativeCommandError text for normal stderr output

- **Status:** RULE
- **Symptom:** A command that worked prints red `NativeCommandError` lines when run with `2>&1` in Windows PowerShell 5.1.
- **Cause:** PowerShell 5.1 wraps every line a program writes to stderr as an error record, even progress messages.
- **Rule:** Judge success by the program's own output and `$LASTEXITCODE`, not by the red text. Avoid `2>&1` unless you need stderr.

## [2026-10-25] Text files corrupted into strange characters

- **Status:** RULE
- **Symptom:** Characters such as é or – turn into Ã© or â€" after a file was rewritten from a script.
- **Cause:** Windows PowerShell 5.1 `Set-Content` and `Out-File` use legacy or BOM encodings; a UTF-8 file read with another code page is garbled on write-back.
- **Rule:** Edit files with the editor tools, or with Python using `encoding="utf-8"`. Never rewrite source files with PowerShell redirection.

## [2026-10-25] First commit fails with "Please tell me who you are"

- **Status:** RULE
- **Symptom:** `work add-repo <name> --init` stops with a Git identity error.
- **Cause:** Git needs a name and email for every commit.
- **Fix:** Run once: `git config --global user.name "Your Name"` and `git config --global user.email you@example.com`, then add the repository again without `--init` (the folder already exists).

## [2026-10-25] New branch based on a stale main

- **Status:** RULE
- **Symptom:** A new branch conflicted heavily because it started from an old local `main`.
- **Cause:** Local branches do not update by themselves.
- **Rule:** `git -C <clone> fetch origin` first, create the work area with `--base origin/main`, and keep the recorded base SHA in the changelog.

## [2026-10-25] Worktree creation is very slow on a huge repository

- **Status:** RULE
- **Symptom:** `work create` takes many minutes or times out.
- **Cause:** A full checkout writes every file of the repository.
- **Rule:** Check out only the folders you need: `work create --repo R --branch B --sparse <folder> <folder>`.

## [2026-10-25] Replacing a just-written file fails with Access is denied (Windows)

- **Status:** WORKAROUND
- **Symptom:** `os.replace` raises `PermissionError: [WinError 5]` now and then, right after a file was written.
- **Cause:** Antivirus or the search indexer opens new files for a moment.
- **Fix:** Retry the swap a few times with short pauses (`src/agent_workbench/infrastructure/files.py`).

## [2026-10-25] Git tests in TemporaryDirectory fail with Access is denied (Windows)

- **Status:** WORKAROUND
- **Symptom:** Tests that run Git inside `tempfile.TemporaryDirectory()` fail with `PermissionError: [WinError 5] Access is denied` on `.git`, often during cleanup.
- **Cause:** Recent Python versions on Windows create that folder with owner-only permissions (mode 0o700); files Git creates inside it can become unreadable even to the test.
- **Fix:** Create test folders with a plain `mkdir()` under `tempfile.gettempdir()` and delete them with a handler that clears read-only flags (`tests/support.py`).

## [2026-10-25] Quoted arguments break in Windows PowerShell

- **Status:** RULE
- **Symptom:** Commands with JSON or nested quotes fail or split arguments in Windows PowerShell 5.1; `&&` between commands is rejected.
- **Cause:** PowerShell 5.1 passes embedded double quotes (`\"`) to native programs inconsistently and does not support `&&`.
- **Rule:** Prefer `key=value` arguments, single-quoted patterns, or a JSON file passed by path. Never put `\"` inside a double-quoted argument. Run commands one at a time, or separate them with `;`.
