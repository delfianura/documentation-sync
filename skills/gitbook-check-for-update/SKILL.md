---
name: gitbook-check-for-update
description: Read-only analysis of GitBook documentation gaps against gl-sdk code changes. Use to check whether a PR, branch, commit, or the whole main branch needs GitBook updates, before running gitbook-update.
---

# GitBook Documentation Update Check

Performs **read-only analysis** to validate GitBook documentation completeness against the codebase using:

1. **Mode 1 (PR/Branch/Commit)**: Compare specific changes against `main` → targeted update recommendations
2. **Mode 2 (Full Audit)**: Analyze entire `main` branch → comprehensive gap analysis

User input: `$ARGUMENTS`

---

## Core Rules

### Documentation Generalization

- **Feature-focused, not implementation-specific**: Frame as "Add video embedding support" not "Add TwelveLabs section"
- **Integration over new sections**: Integrate into existing sections when possible
- **Minimal implementation details**: Put implementation details in hint boxes, focus on core functionality
- **Avoid redundancy**: Check existing structure before recommending new sections

### Mode Detection

```
if (PR number OR PR URL provided):
  → Mode 1: PR-based Analysis
elif (branch name OR commit SHA provided):
  → Mode 1: Branch/Commit Analysis
elif (no input provided OR "audit"/"full analysis" keywords):
  → Mode 2: Full Audit

```

- Only ask for clarification if genuinely ambiguous (e.g., "check X" without context)
- Default to Mode 2 (Full Audit) if input is empty

### Section Discovery — Classification Table

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

A discovered section is represented as a `(product, type, path)` tuple:

```
{ product: "gen-ai-sdk",          type: "tutorial",  path: "gitbook/gen-ai-sdk/tutorials/" }
{ product: "gl-ai-agent-package", type: "guide",     path: "gitbook/gl-ai-agent-package/guides/" }
{ product: "common-modules",      type: "resource",  path: "gitbook/common-modules/design-patterns/" }
```

---

## Mode 1: PR/Branch/Commit Analysis Flow

### Step 1.1: Extract code changes

- **If PR URL provided**: Fetch diff using GitHub API or web scraping
- **If branch name provided**: Run `git diff main...HEAD --name-only` to get changed files
- **If commit SHA provided**: Run `git diff <commit>^..<commit> --name-only` to get changed files
- Run full diff: `git diff main...HEAD` (or equivalent for commit)
- Filter for files in `libs/` directory only
- If no `libs/` files changed, output "No documentation update needed" and stop

### Step 1.2: Identify changed components and modules

- For each changed file in `libs/`:
  - Extract module name (e.g., `libs/gllm-inference/` → `gllm-inference`)
  - Extract submodule path (e.g., `gllm_inference/em_invoker/cohere_em_invoker.py` → `em_invoker`)
  - Extract component name (e.g., `CohereEMInvoker`)
  - Classify change type: [added, modified, deleted]
- Build component metadata map:
  ```python
  {
    "gllm-inference": {
      "submodules": ["em_invoker", "builder"],
      "files_changed": ["gllm_inference/em_invoker/cohere_em_invoker.py"],
      "components": ["CohereEMInvoker"],
      "change_types": ["modified"],
      "api_changes": ["new_parameter"],
      "feature_impact": ["Custom endpoint support"]
    }
  }
  ```

### Step 1.3: Detect API changes from diff analysis

- Parse Python code changes to identify:
  - **New parameters**: Added function/method parameters
  - **Signature changes**: Modified parameter types or defaults
  - **New classes/methods**: Added classes or methods
  - **Removed features**: Deleted classes, methods, or parameters
  - **Breaking changes**: Changes that affect existing API contracts
- Map changes to **features** (not implementation):
  - `base_url` parameter → "Custom endpoint support"
  - `streaming=True` → "Streaming response support"
  - New `ErrorParser` class → "Unified error handling"
- Use simple pattern matching on diff:
  - Look for `def __init__` changes for constructor updates
  - Look for `def method_name` additions for new methods
  - Look for docstring changes indicating API updates

### Step 1.4: Discover GitBook sections and scan for coverage

#### Discover all sections dynamically

- Checkout `docs/gitbook-sync` branch: `git checkout docs/gitbook-sync`
- Walk `gitbook/` one level deep to list product directories
- For each product directory, walk one more level to list section subdirectories
- Classify each section using the Classification Table above
- Retain only sections with included types (`tutorial`, `guide`, `resource`)
- Result: a list of `(product, type, path)` tuples covering the full gitbook

#### Search for coverage across all discovered sections

For each changed component, search across **all discovered sections**:

```bash
grep -r "ComponentName" gitbook/ --include="*.md" -n
grep -r "submodule_name" gitbook/ --include="*.md" -n
grep -r "module-name"    gitbook/ --include="*.md" -n
```

- Build: `{ section_path → [matching_files_with_line_numbers] }`
- Each matched file carries its section type (derived from its parent directory name using the classification table)

### Step 1.5: Analyze documentation relevance and gaps

For each documentation file that mentions changed components:

- Calculate relevance score (0-100%):
  - 90-100%: Feature is primary focus (in title, multiple examples)
  - 70-89%: Feature is heavily used (in code examples, parameter tables)
  - 40-69%: Feature is mentioned (in prerequisites, related sections)
  - 0-39%: Feature is briefly referenced
- Extract context:
  - **Prerequisites section**: Check if component is listed
  - **Code examples**: Find code blocks using the component
  - **Parameter tables**: Find tables documenting component parameters
  - **API references**: Find links to API documentation
- Identify section type from the matched file's parent directory

### Step 1.6: Generate suggested updates

- Based on API changes detected, suggest specific updates:
  - If **new_parameter**: "Add `parameter_name` to constructor table and code examples"
  - If **signature_change**: "Update method signature in API reference"
  - If **new_class**: "Add new class documentation section"
  - If **breaking_change**: "Add migration note and update examples"
  - If **new_feature**: "Add feature to 'Capabilities' section with example"
  - **Priority**: High/Medium/Low based on:
    - High: Breaking changes, new major features, security updates, frequently-used features
    - Medium: New parameters, minor features, documentation gaps
    - Low: Clarifications, examples, minor improvements
  - **Integration Strategy**: Specify whether to:
    - Integrate into existing section (preferred)
    - Create new subsection within existing section
    - Create new top-level section (only for genuinely new feature categories)
  - **Generalization Notes**: Remind to:
    - Use general section titles (feature/capability, not implementation)
    - Put implementation details in hints
    - Keep examples minimal and focused

### Step 1.7: Output structured update report (Mode 1)

Generate report using the "Output Report" section below.

---

## Mode 2: Full Audit Analysis Flow

### Step 2.1: Discover all GitBook sections

- Checkout `docs/gitbook-sync` branch: `git checkout docs/gitbook-sync`
- Walk `gitbook/` to discover all sections using the same classification as Step 1.4
- Retain only sections with included types (`tutorial`, `guide`, `resource`)
- Result: complete list of `(product, type, path)` tuples covering the full gitbook

### Step 2.2: Scan all discovered sections for documentation coverage

- For each discovered section from Step 2.1:
  - Search for all module/component names from `libs/` within that section path
  - Run: `grep -r "ComponentName" <section_path> --include="*.md" -n`
  - Build list of files that mention each component/feature

### Step 2.3: Classify coverage per section

For each module in `libs/` × each discovered section:

- If not found in any doc: Mark as "UNDOCUMENTED"
- If found but examples don't match current code: Mark as "OUTDATED"
- If found and current: Mark as "DOCUMENTED"
- If documentation exists but component no longer in code: Mark as "ORPHANED"

### Step 2.4: Full audit gap analysis

- Perform comprehensive gap analysis across all discovered sections:
  - **Undocumented Features**: Features in code but not found in any documentation section
  - **Orphaned Documentation**: Documentation pages without corresponding code
  - **Outdated Examples**: Code examples using old API versions (compare against current code)
  - **Missing Migration Guides**: Breaking changes without migration documentation
- Prioritize gaps by:
  - Feature importance (core vs optional)
  - Usage frequency (inferred from code patterns)
  - Impact on users (breaking changes > new features > minor updates)
- Output as structured gap report with actionable recommendations

### Step 2.5: Output structured update report (Mode 2)

Generate report using the "Output Report" section below.

---

## Output Report

Use a **single unified format** that adapts to the mode. Format as markdown:

```markdown
# GitBook Update Report

**Mode**: [PR-based | Branch-based | Commit-based | Full Audit]
**PR**: #<number> - <title> (PR-based mode only)
**Branch**: <branch-name> (Branch/Commit-based mode only)
**Restricted Branch**: ⚠️ docs/gitbook-sync (if applicable)
**Changed Components**: <module-list>

## Summary

- **Total Files Changed**: <count>
- **Libs Modules Affected**: <module-list>
- **Documentation Sections Affected**: <count>
- **Priority**: [CRITICAL/HIGH/MEDIUM/LOW]

---

## Component Analysis (File-based modes only)

**Module**: <module-name>
**Submodules**: <submodule-list>
**Components**: <component-list>
**Change Types**: <change-type-list>
**API Changes**:

- <change-description>

---

## Documentation Impact

### 🟡 Tutorials (<count> files)

#### [PRIORITY] <product>/<section-type>/<file-path>

- **Product**: <product-name>
- **Module**: <module-name>
- **Relevance**: <percentage>%
- **Mentions**: Line <number>: "<context>"
- **Suggested Updates**: [ ] <specific-update>

### 🔴 How-to Guides (<count> files)

#### [PRIORITY] <product>/<section-type>/<file-path>

- **Product**: <product-name>
- **Module**: <module-name>
- **Relevance**: <percentage>%
- **Mentions**: Line <number>: "<context>"
- **Suggested Updates**: [ ] <specific-update>

### 🟢 Resources (<count> files)

#### [PRIORITY] <product>/<section-type>/<file-path>

- **Product**: <product-name>
- **Module**: <module-name>
- **Relevance**: <percentage>%
- **Suggested Updates**: [ ] <specific-update>

---

## Section Coverage Matrix (Full Audit only)

| Module | <product-a>/tutorials | <product-a>/guides | <product-b>/guides | <product-c>/tutorials | ... |
| ------ | --------------------- | ------------------ | ------------------ | --------------------- | --- |
| <module-1> | ✅ | ✅ | ⚠️ outdated | ❌ | |
| <module-2> | ✅ | ❌ | ❌ | ✅ | |

Only sections with at least one match are included in the matrix.

---

## Next Steps

Run the gitbook update workflow to update all relevant GitBook documentation sections based on this analysis.
```

## Mode-Specific Adaptations

### File-Based Modes (PR/Branch/Commit)

Include all sections above. Focus on:

- Specific files changed
- Exact line numbers in documentation
- Component analysis

### Full Audit Mode (No Input)

Adapt the report:

- Replace "Component Analysis" with "Coverage Analysis by Module"
- Add "Section Coverage Matrix" showing module × section grid
- Add "Recommended Actions" section with phased plan
- Show coverage percentages per module
- List undocumented features, outdated examples

### Restricted Branch Mode (docs/gitbook-sync)

Add prominent warning:

```markdown
## ⚠️ IMPORTANT: Restricted Branch Notice

This branch targets `docs/gitbook-sync`, which is **NOT mergeable into `main`**.
```

Then use standard format but emphasize sync recommendations.

## Workflow Execution Checklist

- [ ] User input parsed correctly (PR/branch/commit/none)
- [ ] Correct mode selected (PR/Branch/Commit/Audit/Restricted)
- [ ] Code changes extracted (Mode 1 only)
- [ ] Features identified and mapped
- [ ] GitBook sections discovered dynamically
- [ ] All discovered sections searched for coverage
- [ ] Gaps identified and prioritized
- [ ] Recommendations generated
- [ ] Report formatted and output
- [ ] Next steps provided (gitbook update workflow reference)
