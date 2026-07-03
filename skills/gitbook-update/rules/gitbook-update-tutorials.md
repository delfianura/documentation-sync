# GitBook Tutorial Documentation Rules

This rule should be applied when updating tutorial documentation in any `tutorials/` section across the gitbook. Tutorials are component-focused documentation with detailed API references and usage examples.

## When to Apply This Rule

This rule applies to **any** GitBook section of this type, regardless of which product it lives under. The same rules govern `gen-ai-sdk/tutorials/`, `gl-ai-agent-package/tutorials/`, `common-modules/tutorials/`, `gl-deep-researcher/tutorials/`, `gl-meemo/tutorials/`, etc.

Apply this rule when:

- Updating existing tutorial files in any `gitbook/<product>/tutorials/` directory
- Creating new tutorial documentation for components
- Modifying code examples, parameter tables, or API references in tutorials
- Adding new features or capabilities to component documentation

## Critical Generalization Rules

⚠️ **Always keep documentation GENERAL, not implementation-specific:**

### 1. Section Titles Must Be General

- ❌ WRONG: "Video Embedding with TwelveLabs", "Chunking with RecursiveChunker"
- ✅ CORRECT: "Video Embedding", "Multimodal Input", "Chunking Strategies"
- Section titles should describe the FEATURE/CAPABILITY, not the specific IMPLEMENTATION

### 2. Integrate Into Existing Sections

- ❌ WRONG: Create new top-level section for implementation-specific features
- ✅ CORRECT: Add to existing relevant sections (e.g., add new chunking method to "Chunking Strategies")
- Only create new sections for genuinely NEW feature categories

### 3. No Redundant Headers

- ❌ WRONG: Add "Setup" subsection when Prerequisites already exists
- ✅ CORRECT: Update existing Prerequisites section
- Check if a section already exists before creating a new one

### 4. Implementation Details in Hints Only

- ❌ WRONG: Detailed implementation-specific subsections ("Supported Input Types", "All Configuration Options")
- ✅ CORRECT: Brief example + hint box for implementation-specific details
- Keep implementation-specific information minimal and contained

### 5. Focus on Core Features

- ❌ WRONG: Document every implementation-specific parameter and option
- ✅ CORRECT: Show basic usage, mention advanced options exist
- Avoid over-documentation of implementation-specific details

### 6. Example Pattern

```markdown
## [Feature Name]

You can [perform action]:

\`\`\`python

# Generic example showing the capability

component = ComponentClass(config)
result = component.method(input)
\`\`\`

{% hint style="info" %}
**Implementation Notes**: [Specific feature] is supported by `SpecificImplementation`.
See [docs](link) for additional options.
{% endhint %}
```

## Tutorial Structure

Tutorials must follow this standard structure:

### 1. Front Matter

```markdown
---
icon: [icon-name] # e.g., subtitles, file-import, messages-question
---
```

### 2. Title and Header Links

```markdown
# [Component Name]

[**`module-name`**](github-link) | **Tutorial**: [file.md](file.md "mention") | **Use Case**: [guide-link](guide-link "mention") | [API Reference](api-link)
```

### 3. What's a Component Section

- Conceptual explanation (2-3 paragraphs)
- Optional diagram or example output

### 4. Prerequisites

```markdown
<details>
<summary>Prerequisites</summary>

This example specifically requires completion of all setup steps listed on the [prerequisites.md](../../gen-ai-sdk/prerequisites.md "mention") page.

[Optional: List specific prerequisites]

- Prerequisite 1
- Prerequisite 2
</details>
```

### 5. Installation

Use tabs for different OS:

```markdown
{% tabs %}
{% tab title="Linux, macOS, or Windows WSL" %}
\`\`\`bash
pip install --extra-index-url https://oauth2accesstoken:$(gcloud auth print-access-token)@glsdk.gdplabs.id/gen-ai-internal/simple/ [package-name]
\`\`\`
{% endtab %}
{% endtabs %}
```

### 6. Quickstart

- Brief introduction
- Basic code example
- Expected output
- Brief explanation

### 7. Feature Sections

- Detailed feature explanations
- Code examples with comments
- Practical use cases

### 8. Advanced Usage (Optional)

- Advanced patterns
- Customization options
- Complex use cases

### 9. Migration Guide (Optional)

- Only for breaking changes
- Show before/after examples

### 10. API Reference

- Links to detailed API documentation

## Section-Specific Update Guidelines

### For Prerequisites Section

- Check if new dependencies were added
- Update package version requirements if changed
- Add new setup steps if required
- Format as checklist with `- [ ]`

### For Installation Section

- Update package installation commands if version changed
- Add new extras if dependencies added
- Maintain OS-specific tabs (Linux/macOS, Windows PowerShell, Windows CMD)

### For Quickstart Section

- Update basic code example with new parameters
- Keep example simple and focused on core usage
- Add comments explaining new parameters

### For Parameter Tables

- Add new parameters to existing tables
- Update parameter descriptions if changed
- Mark parameters as Required/Optional
- Format:

```markdown
| Parameter      | Type | Required | Description               |
| -------------- | ---- | -------- | ------------------------- |
| existing_param | str  | Yes      | Existing description      |
| new_param      | str  | No       | New parameter description |
```

### For Feature Sections

- If new method added, create new subsection
- If existing method changed, update code examples
- Include before/after examples for clarity
- Add practical use cases

### For Migration Guide

- If breaking changes detected, add migration section
- Show old vs new usage patterns
- Provide step-by-step migration instructions

## Folder Organization Rules

### When to Create a Folder vs Single File

**Create a FOLDER when:**

1. Component has **multiple sub-components** (e.g., `lm-invoker/` contains multiple invoker types)
2. Component has **migration guides** or **version-specific docs**
3. Component is a **category/module** with multiple related components (e.g., `inference/`, `retrieval/`)
4. Component has **multiple related tutorials** that share a common theme

**Use SINGLE FILE when:**

1. Component is **standalone** with no sub-components (e.g., `em-invoker.md`, `prompt-builder.md`)
2. Component is **simple** and doesn't require extensive documentation
3. Component is a **specific feature** of a larger module

### Folder Naming Conventions

- Use **kebab-case** for all folders and files (e.g., `lm-request-processor`, `your-first-rag-pipeline.md`)
- Folder names should be **descriptive** and match the component/module name
- For category folders, use **plural** if it contains multiple items (e.g., `tutorials/`)
- For component folders, use **singular** (e.g., `loader/`, `retriever/`)

## Common Mistakes to Avoid

❌ **Mistake 1: Implementation-Specific Section Titles**

- Don't create sections like "Video Embedding with TwelveLabs", "Chunking with RecursiveChunker"
- Use general titles: "Video Embedding", "Multimodal Input", "Chunking Strategies"

❌ **Mistake 2: Creating Redundant Sections**

- Don't add "Setup" when Prerequisites exists
- Don't add "Installation" when it already exists
- Always check existing structure first

❌ **Mistake 3: Over-Documenting Implementation Details**

- Don't create subsections for "Supported Input Types", "All Configuration Options"
- Keep implementation-specific details in hint boxes
- Focus on the core feature, not every parameter

❌ **Mistake 4: Creating New Top-Level Sections**

- Don't create new sections for implementation-specific features
- Integrate into existing relevant sections
- Only create new sections for genuinely new feature categories

## Best Practice: Integration Pattern

1. Find the most relevant existing section
2. Add a brief subsection or paragraph
3. Show one clear example demonstrating the capability
4. Put implementation-specific details in a hint box
5. Keep it concise and general

## Implementation Guidelines

1. **Apply changes directly**
   - Use edit tools to modify files immediately
   - Make changes section by section in logical order
   - Preserve existing formatting and structure
   - Maintain consistent markdown style

2. **Verify changes**
   - Briefly read key sections after editing
   - Ensure markdown syntax is valid
   - Verify code blocks are properly formatted

3. **Report completion**
   - Provide concise summary of changes made
   - List sections that were updated
   - Suggest next steps (testing, related docs)
