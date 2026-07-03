---
name: gitbook-update
description: Orchestrates GitBook documentation updates for gl-sdk (Tutorials, How-to Guides, Resources) from a PR/branch or file list. Creates a docs/gitbook-sync-based branch in a worktree, edits gitbook/ only, and opens a PR against docs/gitbook-sync. Depends on gitbook-check-for-update. Use whenever asked to update GitBook / docs for a gl-sdk change.
---

# GitBook Content Update Workflow

This unified workflow orchestrates GitBook updates across Tutorials, How-to Guides, and Resources. It will re-identify relevant changes and either:

- Use the output from the gitbook check-for-update workflow if provided, or
- Perform its own classification to decide which sections to update.

The user input to you can be provided directly by the agent or as a command argument — you MUST consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

**Input Detection**: The workflow supports two modes:

1. **PR/Branch Mode** (default): User provides PR number, URL, or branch name → analyze git diff
2. **File-Based Mode**: User provides file paths from `libs/` and docs target branch name (optional) → analyze file content directly

Detect which mode to use based on user input.

## High-Level Flow

1. Re-identify changes from PR/branch
2. Discover all GitBook sections dynamically
3. Determine impacted documentation sections by type
4. For each impacted section, update files by following the section-type-specific rules
5. Cherry-pick documentation commits (if applicable)
6. Verify branch cleanliness (docs-only enforcement)
7. Commit changes to docs branch with strict conventional format
8. Create PR via GitHub CLI targeting `docs/gitbook-sync`. The docs PR **must reference source commits**, but **must not merge the feature branch**

---

## Section Discovery — Classification Table

When walking `gitbook/` to discover sections, classify each subdirectory by name:

| Directory name           | Section type          | Include in updates? |
| ------------------------ | --------------------- | ------------------- |
| `tutorials`              | Tutorial              | ✅ Yes              |
| `guides`                 | How-to Guide          | ✅ Yes              |
| `resources`              | Resource              | ✅ Yes              |
| `design-patterns`        | Resource (conceptual) | ✅ Yes              |
| `getting-started`        | Onboarding            | ❌ Skip             |
| `rest-api-reference`     | API Reference         | ❌ Skip             |
| `sdk`                    | SDK Reference         | ❌ Skip             |
| `gl-connectors` (nested) | Reference             | ❌ Skip             |

---

## Step 1 — Re-identify Changes

### Mode A: PR/Branch Mode (Default)

- If the user provides the structured report output from the check-for-update workflow, parse and use it directly.
- Otherwise, re-run classification inline using the same principles:
  - Parse PR number/URL or compare current branch vs target (default: main)
  - Extract changed files under `libs/`
  - Detect API changes (new parameters, new methods, signature/breaking changes)
  - **Discover all GitBook sections dynamically**:
    1. Checkout `docs/gitbook-sync` branch
    2. Walk `gitbook/` one level deep → product directories
    3. Walk each product one level → section directories
    4. Classify each section using the Classification Table above
    5. Retain only included types
  - Search across **all discovered sections** for component/module references:
    ```bash
    grep -r "ComponentName" gitbook/ --include="*.md" -n
    ```
  - Build an impact set of candidate files per section with a priority

### Mode B: File-Based Mode

**Trigger**: User provides file paths (e.g., "update docs based on `libs/gllm-inference/gllm_inference/lm_invoker/openai_lm_invoker.py`")

**Process**:

1. **Extract Component Metadata**
   - Parse file paths to identify:
     - Module: `libs/gllm-inference/` → `gllm-inference`
     - Submodule: `gllm_inference/lm_invoker/` → `lm_invoker`
     - Component: `openai_lm_invoker.py` → `OpenAILMInvoker`
   - Read file content to understand:
     - Class/function signatures
     - Public API methods
     - Constructor parameters
     - Key features and capabilities

2. **Discover All GitBook Sections and Scan for Coverage**
   - Checkout `docs/gitbook-sync` branch:
     ```bash
     git checkout docs/gitbook-sync
     git pull origin docs/gitbook-sync
     ```
   - Discover all sections dynamically (same as Mode A above)
   - Search for component mentions across **all discovered sections**:
     ```bash
     grep -r "OpenAILMInvoker" gitbook/ --include="*.md" -n
     grep -r "lm_invoker" gitbook/ --include="*.md" -n
     grep -r "gllm-inference" gitbook/ --include="*.md" -n
     ```
   - Build a map of existing documentation:
     - Which files mention the component (with their product and section type)
     - What sections cover related features
     - What's currently documented vs what's in the code

3. **Identify Documentation Gaps**
   - Compare current file content with existing documentation:
     - **Missing features**: Methods/parameters in code but not in docs
     - **Outdated examples**: Code patterns that don't match current implementation
     - **Incomplete coverage**: Features mentioned but not explained
     - **New capabilities**: Functionality that has no documentation
   - Categorize gaps by documentation type:
     - **Tutorial gaps**: Missing quickstart, basic usage, or feature sections
     - **How-to gaps**: Missing task-oriented guides using the component
     - **Resource gaps**: Missing model lists, configuration references, or feature matrices

4. **Build Update Recommendations**
   - For each gap, determine:
     - **Section type**: Tutorial / How-to / Resource (from discovered section classification)
     - **Priority**: High (missing core features) / Medium (incomplete coverage) / Low (enhancements)
     - **Integration strategy**: Add to existing section vs create new section
     - **Specific actions**: What needs to be added/updated

5. **Present Recommendations to User (REQUIRED CONFIRMATION)**
   - Display structured report:

     ```markdown
     # Documentation Update Plan

     **Target Branch**: docs/<generated-branch-name>

     **Files Analyzed**:

     - libs/gllm-inference/gllm_inference/lm_invoker/openai_lm_invoker.py

     **Existing Documentation Found**:

     - gen-ai-sdk/tutorials/inference/lm-invoker.md (mentions OpenAILMInvoker)
     - gl-ai-agent-package/guides/language-models.md (mentions LMInvoker)
     - gl-smart-search/resources/supported-models.md (lists OpenAI models)

     **Identified Gaps**:

     ### High Priority

     - [ ] **Tutorial** (gen-ai-sdk): Add streaming support section
     - [ ] **Tutorial** (gen-ai-sdk): Update constructor parameters table

     ### Medium Priority

     - [ ] **How-to** (gl-ai-agent-package): Update guide with new parameters
     - [ ] **Resource** (gl-smart-search): Add note about rate limiting

     **Proposed Updates**:

     1. Update `gitbook/gen-ai-sdk/tutorials/inference/lm-invoker.md`
     2. Update `gitbook/gl-ai-agent-package/guides/language-models.md`
     3. Update `gitbook/gl-smart-search/resources/supported-models.md`

     **Proceed with these updates? (yes/no)**
     ```

   - **WAIT FOR USER CONFIRMATION** before proceeding to Step 2
   - Allow user to:
     - Approve all updates: respond with "yes"
     - Select specific updates only: respond with "yes" and list selected items
     - Request modifications to the plan: respond with "no" and explain changes needed

**Notes**:

- File-based mode focuses on **documentation completeness** rather than **change tracking**
- Gaps are treated as "diffs" between current code state and documentation state
- User confirmation is **mandatory** before applying any changes
- Follow the same generalization rules: feature-focused, minimal implementation details, integrate into existing sections
- **Reuse existing PRs when possible**: If an open docs PR exists, offer to continue it rather than creating a new one

## Step 2 — Sync branch `docs/gitbook-sync` with `main`

- Sync branch `docs/gitbook-sync` with `main`:
  ```bash
  git checkout docs/gitbook-sync
  git fetch origin main
  git merge origin/main
  git push origin docs/gitbook-sync
  ```
  IMPORTANT: DO NOT PUSH TO docs/gitbook-sync other than this step.

## Step 3 — Setup Docs Branch

- **Determine docs branch name** based on mode:

  **PR-Based Mode (Mode A)**:
  - Derive from current feature branch:
    - `f/feature-name` → `docs/feature-name`
    - `feature-name` → `docs/feature-name`
      `generated-branch-name` = `feature-name`

  **File-Based Mode (Mode B)**:
  - If user selected existing branch:
    - Use branch name from user input (e.g., `docs/sync-gllm-pipeline-steps-func`)
  - If user does not provide an existing branch, create a new branch based on the action:
    - Generate: `docs/<action>-<lib-name>-<component-name>-<part-of-change (optional)>`
      `generated-branch-name` = <action>-<lib-name>-<component-name>-<part-of-change (optional)>
    - Example: `docs/sync-gllm-inference-openai-lm-invoker-parameters`

- Use the feature branch as the **context source** (read-only) to inspect code, diffs, and commits.
- Perform all documentation edits and commits **only on the docs branch**.
- **Docs branches must never be created from the feature branch.**
- Prepare the docs branch:
  - If the branch exists:
    ```bash
    git checkout <branch-name>
    ```
  - If the branch does not exist:
    ```bash
    git checkout docs/gitbook-sync
    git checkout -b <branch-name>
    ```

## Step 4 — Decide Which Files to Update

- Update files **only** under: `gitbook/**`
- Use either the provided check-for-update report or the inline classification from Step 1 to decide which file(s) to update.

### Section Type Routing

For each matched file from the impact set:

1. Determine its **section type** from its path's parent directory name using the Classification Table
2. Apply the corresponding rules file:

   | Section type          | Rules file                                |
   | --------------------- | ----------------------------------------- |
   | Tutorial              | `rules/gitbook-update-tutorials.md`     |
   | How-to Guide          | `rules/gitbook-update-how-to-guides.md` |
   | Resource              | `rules/gitbook-update-resources.md`     |
   | Resource (conceptual) | `rules/gitbook-update-resources.md`     |

3. Files from **any product section** are eligible for updates — not just gen-ai-sdk

Decision criteria (same priority logic):

- HIGH priority matches → update
- MEDIUM priority matches → update if clearly affected
- LOW priority matches → skip unless explicitly requested

### Typical updates by section type

**Tutorials** (following `rules/gitbook-update-tutorials.md`):
- Prerequisites, Installation
- Quickstart and code examples
- Parameter tables and feature sections
- Migration guide for breaking changes
- Keep titles and sections general (feature/capability-focused). Put implementation specifics in hint boxes.

**How-to Guides** (following `rules/gitbook-update-how-to-guides.md`):
- Prerequisites checklist
- Step-by-step instructions with tabs for implementation options
- Troubleshooting and Next Steps
- Keep guides task-oriented and integrate provider/implementation options via tabs/hints.

**Resources** (following `rules/gitbook-update-resources.md`):
- Updating model/provider lists
- Editing feature matrices and configuration references
- Adding short, factual notes without marketing language
- Maintain consistent tables, lists, and neutral tone.

## Step 5 — Apply Changes

- Edit the identified `gitbook/*` files directly.
- Preserve existing structure and formatting.
- Follow generalization rules:
  - Feature-focused titles and sections
  - Integrate into existing sections when possible
  - Keep implementation-specific details minimal and in hints/tabs
  - Avoid redundant sections (e.g., duplicate Setup/Installation)
- **If creating a new file**: register it in the relevant `SUMMARY.md` at the correct position in the table of contents. Every new `.md` file under `gitbook/` must have a corresponding entry in `SUMMARY.md` or it will not appear in the published gitbook.

## Step 6 — Cherry-pick Documentation Commits (If Applicable)

If documentation changes were already committed in the feature branch:

- Cherry-pick **only** the commit(s) that modified `gitbook/**` exclusively:
  ```bash
  git cherry-pick <commit-sha>
  ```
- If a commit contains mixed changes (code + docs), **do not cherry-pick**. Instead, manually apply the documentation changes only.

## Step 7 — Verify Branch Cleanliness (ENFORCED)

**Critical**: The docs branch must contain **only** documentation changes.

- Verify that only documentation files are modified and branch is on docs/<generated-branch-name>, not docs/gitbook-sync or main:
  ```bash
  git status
  ```
- Move to branch docs/<generated-branch-name> if the current branch is not docs/<generated-branch-name>:

  ```bash
  git checkout docs/<generated-branch-name>
  ```

- If any non-`gitbook/**` files appear:
  - Unstage them immediately:
    ```bash
    git reset HEAD <non-gitbook-file>
    ```
  - Or reset and re-add only gitbook files:
    ```bash
    git reset
    git add gitbook/
    ```

- **The docs branch must remain docs-only**. No code, config, or test files allowed.

## Step 8 — Commit Rules (REQUIRED)

- Stage strictly documentation files only:

  ```bash
  git add gitbook/
  ```

- Commit using the exact format:

  ```
  docs(gllm-<library>): <concise description of documentation update>
  ```

  Example: `docs(gllm-inference): Update catalog tutorial with prompt_builder_kwargs and history formatting`

- One logical documentation update per commit.
- Ensure commit message is descriptive and follows conventional commits format.

## Step 9 — Push and Create Pull Request (CLI)

- **Push changes to docs branch**:

DO NOT PUSH TO docs/gitbook-sync directly

```bash
git push origin docs/<generated-branch-name>
```

- **Check if PR already exists**:

  ```bash
  EXISTING_PR=$(gh pr list \
    --base docs/gitbook-sync \
    --head docs/<generated-branch-name> \
    --state open \
    --json url \
    --jq '.[0].url')
  ```

- **Branching behavior based on PR existence**:

  **Case A — PR does NOT exist** (`$EXISTING_PR` is empty):

  **NOTE**:
  - PR Title should be in format of `docs(gllm-<library>): <concise description>` where `<library>` should be inferred from the implementation source code path included in the documentation update.

  Create new Pull Request:

  ```bash
  gh pr create \
    --base docs/gitbook-sync \
    --head docs/<generated-branch-name> \
    --title "docs(gllm-<library>): <concise description>" \
    --draft \
    --body "## Documentation Update

**Related Feature Branch/PR**: #<PR-number> or <branch-name>

**Documented Source Commits**:

- <commit-sha>: <commit summary>
- <commit-sha>: <commit summary>

**Changes**:

- Updated <section> with <feature>
- Added documentation for <capability>

**Sections Modified**:

- [ ] Tutorials
- [ ] How-to Guides
- [ ] Resources"
  ```

  **Case B — PR already exists** (`$EXISTING_PR` has value):

  Reuse existing PR (do NOT create a new one):
  ```bash
  echo "PR already exists: $EXISTING_PR"
  echo "New commits have been pushed to the existing PR."
  ```

- **Output only the Pull Request URL** after creation.
- **Do not** return GitHub compare links.

{% hint style="warning" %}
**Important**:

- Base branch must be `docs/gitbook-sync`, **not** `main`
- PR description must reference the original feature branch/PR
- PR description must list all documented source commits with SHAs
  {% endhint %}

## Validation Checklist

- [ ] Re-identification completed via check-for-update output or inline classification
- [ ] GitBook sections discovered dynamically (not hardcoded)
- [ ] Docs branch created from `docs/gitbook-sync` (not from feature branch)
- [ ] Impacted sections decided by section type routing
- [ ] Updates applied following section-type-specific rules
- [ ] Generalization rules respected (feature-focused, minimal implementation details, no redundant sections)
- [ ] New files registered in `SUMMARY.md` (if any new files were created)
- [ ] Cherry-picked documentation only commits (if applicable)
- [ ] Branch cleanliness verified (only `gitbook/**` files modified)
- [ ] All updated files pass a quick syntax/format scan
- [ ] Changes staged with `git add gitbook/` only
- [ ] Committed with conventional format: `docs(gllm-<library>): <description>`
- [ ] PR created via GitHub CLI targeting `docs/gitbook-sync`
- [ ] PR existence checked before creation attempt
- [ ] PR created via GitHub CLI targeting `docs/gitbook-sync` (if new)
- [ ] Existing PR reused (if already exists)
- [ ] PR description includes feature branch reference and documented commit SHAs
