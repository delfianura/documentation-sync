# GitBook How-to Guide Documentation Rules

This rule should be applied when updating how-to guide documentation in any `guides/` section across the gitbook. How-to guides are task-oriented documentation with step-by-step instructions for real-world use cases.

## When to Apply This Rule

This rule applies to **any** GitBook section of this type, regardless of which product it lives under. The same rules govern `gen-ai-sdk/guides/`, `gl-ai-agent-package/guides/`, `common-modules/guides/`, `gl-deep-researcher/guides/`, `gl-observability/guides/`, `gl-smart-search/guides/`, etc.

Apply this rule when:

- Updating existing how-to guide files in any `gitbook/<product>/guides/` directory
- Creating new task-oriented guides
- Modifying step-by-step instructions or code examples in guides
- Adding new workflow steps or troubleshooting sections

## Critical Generalization Rules

⚠️ **Always keep documentation GENERAL, not implementation-specific:**

### 1. Guide Titles Must Be Task-Focused

- ❌ WRONG: "Building RAG with OpenAI", "Parsing PDFs with PyPDFParser"
- ✅ CORRECT: "Building a RAG Pipeline", "Parsing PDF Documents" (mention implementations in content)
- Titles should describe the TASK, not the specific IMPLEMENTATION

### 2. Integrate Implementation Examples Naturally

- ❌ WRONG: Create separate guides for each implementation/provider
- ✅ CORRECT: One guide showing the task, with implementation options
- Use tabs or hints to show implementation alternatives

### 3. No Redundant Setup Sections

- ❌ WRONG: Add "Setup" when Prerequisites exists
- ✅ CORRECT: Update existing Prerequisites or Project Setup
- Check existing structure before adding new sections

### 4. Implementation Details in Hints/Tabs

- ❌ WRONG: Long implementation-specific subsections
- ✅ CORRECT: Brief examples + hint boxes for specifics
- Use tabs for implementation alternatives when needed

### 5. Focus on the Workflow

- ❌ WRONG: Document every implementation parameter
- ✅ CORRECT: Show the task steps, mention customization exists
- Keep focus on accomplishing the task

### 6. Example Pattern with Tabs

```markdown
## Step 2: Initialize Components

Initialize your component:

{% tabs %}
{% tab title="Implementation A" %}
\`\`\`python
component = ImplementationA(config_param="value")
\`\`\`
{% endtab %}

{% tab title="Implementation B" %}
\`\`\`python
component = ImplementationB(config_param="value")
\`\`\`
{% endtab %}
{% endtabs %}
```

## How-to Guide Structure

How-to guides must follow this standard structure:

### 1. Front Matter

```markdown
---
icon: [icon-name] # e.g., flag-pennant, arrow-progress
---
```

### 2. Title and Overview

```markdown
# [Task Title]

[Brief introduction explaining what this guide will help you accomplish]
```

### 3. Prerequisites

```markdown
<details>
<summary>Prerequisites</summary>

This example specifically requires you to complete all setup steps listed on the [prerequisites.md](../../gen-ai-sdk/prerequisites.md "mention") [and other prerequisite guides].

You should be familiar with these concepts and components:

1. [concept-1](link)
2. [component-1](link)
3. [component-2](link)
</details>
```

### 4. Cookbook Reference (if applicable)

```markdown
{% include "../../.gitbook/includes/cookbook.md" %}

<a href="[github-cookbook-link]" class="button primary" data-icon="github">View full project code on GitHub</a>
```

### 5. Installation

Use tabs for different OS (same as tutorials)

### 6. Project Setup

```markdown
{% stepper %}
{% step %}
**Folder Structure**
[Describe the folder structure needed]
{% endstep %}

{% step %}
**Prepare your `.env` file**:
[Environment variables needed]
{% endstep %}
{% endstepper %}
```

### 7. Step-by-Step Instructions

```markdown
## 1) [First Major Step]

{% stepper %}
{% step %}
**[Sub-step title]**
[Instructions]
\`\`\`python

# Code example

\`\`\`
{% endstep %}
{% endstepper %}

## 2) [Second Major Step]

[Continue with numbered steps...]
```

### 8. Troubleshooting (Optional)

```markdown
## Troubleshooting

### Issue: [Error description]

**Cause**: [Why this happens]
**Solution**:
\`\`\`python

# Fixed code

\`\`\`
```

### 9. Next Steps

```markdown
## Next Steps

[Suggest what the user can do next or related guides to explore]
```

## Section-Specific Update Guidelines

### For Overview Section

- Update if the guide's purpose changed
- Add note about new capabilities if relevant
- Keep overview concise and focused on the task

### For Prerequisites Section

- Check if new dependencies or setup steps are needed
- Update component version requirements
- Add new prerequisite items if required
- Format as checklist with `- [ ]`

### For Step-by-Step Instructions

- Update code examples in each step that uses the changed component
- Add new steps if new functionality requires additional actions
- Update step descriptions if workflow changed
- Keep steps focused on the task at hand

### For Code Examples

- Update all code examples that use the changed component
- Add comments explaining new parameters or usage
- Ensure examples are complete and runnable
- Maintain consistent code style with existing examples
- Show practical, real-world usage

### For Troubleshooting Section

- Add new troubleshooting items if breaking changes introduced
- Update error messages if they changed
- Provide solutions for common issues with new features

### For Next Steps Section

- Add links to new related guides if created
- Update links if guide structure changed
- Keep suggestions relevant to the user's journey

## Common Mistakes to Avoid

❌ **Mistake 1: Implementation-Specific Guide Titles**

- Don't create guides like "Building RAG with OpenAI", "Parsing PDFs with PyPDFParser"
- Use task-focused titles: "Building a RAG Pipeline", "Parsing PDF Documents"

❌ **Mistake 2: Creating Redundant Sections**

- Don't add "Setup" when Prerequisites or Project Setup exists
- Don't duplicate Installation sections
- Always check existing structure first

❌ **Mistake 3: Over-Documenting Implementation Details**

- Don't create separate subsections for each implementation's options
- Use tabs or hints for implementation alternatives
- Focus on the task workflow, not implementation specifics

❌ **Mistake 4: Creating Implementation-Specific Guides**

- Don't create separate guides for different implementations
- One guide should work for multiple implementations
- Use tabs to show implementation alternatives

## Best Practice: Multi-Implementation Pattern

1. Write task-focused guide title and introduction
2. Use tabs to show implementation alternatives in code examples
3. Put implementation-specific requirements in hints
4. Keep the workflow general and reusable
5. Link to implementation docs for advanced customization

## Special Considerations for How-to Guides

### 1. Task-Oriented Focus

- Keep changes focused on helping users accomplish the task
- Don't add unnecessary complexity
- Explain new features in context of the task

### 2. User Journey

- Ensure changes don't break the step-by-step flow
- Update step numbers if steps are added/removed
- Keep the guide's narrative coherent

### 3. Practical Examples

- Use realistic, runnable code examples
- Show both basic and advanced usage when relevant
- Include comments that explain the "why" not just the "what"

### 4. Minimal Disruption

- If changes are minor, integrate them smoothly
- If changes are major, consider adding a note at the top
- Preserve the guide's original intent and structure

## Implementation Guidelines

1. **Apply changes directly**
   - Use edit tools to modify files immediately
   - Make changes section by section in logical order
   - Preserve existing formatting and structure
   - Maintain the step-by-step flow

2. **Verify changes**
   - Briefly read key sections after editing
   - Check that markdown syntax is valid
   - Ensure code blocks are properly formatted
   - Verify step numbering is still correct

3. **Report completion**
   - Provide concise summary of changes made
   - List sections that were updated
   - Suggest testing the guide and checking related guides
