# GitBook Resource Documentation Rules

This rule should be applied when updating resource documentation in any `resources/` or `design-patterns/` section across the gitbook. Resources are reference material including model lists, supported features, and conceptual overviews.

## When to Apply This Rule

This rule applies to **any** GitBook section of this type, regardless of which product it lives under. The same rules govern `gen-ai-sdk/resources/`, `gl-ai-agent-package/resources/`, `gl-aip/resources/`, `gl-smart-search/resources/`, `common-modules/design-patterns/`, etc.

Directories named `design-patterns/` follow the same Type B (Conceptual Resource) structure described below.

Apply this rule when:

- Updating existing resource files in any `gitbook/<product>/resources/` or `gitbook/<product>/design-patterns/` directory
- Creating new reference documentation
- Modifying model lists, feature matrices, or configuration references
- Adding new providers, integrations, or capabilities to reference docs

## Critical Generalization Rules

⚠️ **Always keep documentation GENERAL, not implementation-specific:**

### 1. Resource Titles Must Be General

- ❌ WRONG: "OpenAI Models", "RecursiveChunker Options"
- ✅ CORRECT: "Supported Models", "Chunking Options" (with implementation sections)
- Titles should describe the RESOURCE TYPE, not a single implementation

### 2. Organize by Category, Not Implementation

- ❌ WRONG: Separate pages for each implementation/provider
- ✅ CORRECT: One resource with implementation sections
- Use consistent table structure across implementations

### 3. No Redundant Sections

- ❌ WRONG: Add "Setup" or "Installation" to reference docs
- ✅ CORRECT: Keep resources focused on reference information
- Link to tutorials for setup instructions

### 4. Implementation Details in Tables/Sections

- ❌ WRONG: Long prose about each implementation
- ✅ CORRECT: Structured tables with consistent fields
- Keep descriptions brief and factual

### 5. Focus on Facts, Not Features

- ❌ WRONG: Marketing language about implementation capabilities
- ✅ CORRECT: Factual information (IDs, parameters, limits, supported formats)
- Avoid over-selling or comparing implementations

### 6. Example Pattern

```markdown
## [Resource Category]

### **Implementation A**

<table data-header-hidden><thead><tr><th width="197"></th><th></th></tr></thead><tbody>
<tr><td><strong>Field 1</strong></td><td>value</td></tr>
<tr><td><strong>Field 2</strong></td><td>value</td></tr>
<tr><td><strong>Field 3</strong></td><td>value</td></tr>
</tbody></table>

### **Implementation B**

<table data-header-hidden><thead><tr><th width="197"></th><th></th></tr></thead><tbody>
<tr><td><strong>Field 1</strong></td><td>value</td></tr>
<tr><td><strong>Field 2</strong></td><td>value</td></tr>
<tr><td><strong>Field 3</strong></td><td>value</td></tr>
</tbody></table>
```

## Resource Structure

Resources follow different structures based on type:

### Type A: List/Table Resource (e.g., Supported Models)

```markdown
---
icon: [icon-name] # e.g., gear
---

# [Resource Title]

[Brief introduction explaining what this resource provides]

## [Category 1]

[Brief description of this category]

### **[Provider/Item Name]**

<table data-header-hidden><thead><tr><th width="197.0390625"></th><th></th></tr></thead><tbody>
<tr><td><strong>Field 1</strong></td><td>[value]</td></tr>
<tr><td><strong>Field 2</strong></td><td>[value]</td></tr>
<tr><td><strong>Field 3</strong></td><td>[value]</td></tr>
</tbody></table>

### **[Next Provider/Item]**

[Repeat table structure...]

## [Category 2]

[Continue with other categories...]
```

### Type B: Conceptual Resource (e.g., Introduction to RAG)

```markdown
---
icon: [icon-name] # e.g., memo
---

# [Concept Title]

## What is [Concept]?

[Detailed explanation of the concept, 2-3 paragraphs]

[Optional: Include diagrams]

<figure><img src="[image-path]" alt=""><figcaption><p>[Caption]</p></figcaption></figure>

## [Key Aspect 1]

[Explanation with optional stepper for processes]

{% stepper %}
{% step %}
**[Step Name]**
[Description]
{% endstep %}
{% endstepper %}

## [Key Aspect 2]

[Continue with other aspects...]

## [When to Use / Best Practices]

[Practical guidance]
```

## Resource-Specific Update Patterns

### For supported-models.md

**Structure**:

```markdown
# Supported Models

## Language Models

### [Provider Name]

- model-name-1
- model-name-2

## Embedding Models

### [Provider Name]

- embedding-model-1
- embedding-model-2
```

**Update patterns**:

- **New provider**: Add new subsection under appropriate category
- **New model**: Add to existing provider's model list
- **New capability**: Add note about feature support
- **Configuration change**: Add note about custom configuration

**Example update**:

```markdown
### Cohere

- embed-english-v3.0
- embed-multilingual-v3.0
- embed-english-light-v3.0

> **Note**: Cohere embedding models support custom API endpoints via the `base_url` parameter. See [em-invoker.md](../tutorials/inference/em-invoker.md) for usage examples.
```

### For supported-documents.md

**Structure**:

```markdown
# Supported Documents

## Document Formats

| Format | Extension | Support Level | Notes |
| ------ | --------- | ------------- | ----- |
```

**Update patterns**:

- **New format**: Add row to table with format, extension, support level, notes
- **Enhanced support**: Update support level column (Full / Partial / Experimental)
- **New feature**: Add note in Notes column

### For supported-vector-data-store.md

**Structure**:

```markdown
# Supported Vector Data Store

## Available Integrations

- [Store Name]: Description
```

**Update patterns**:

- **New integration**: Add to list with name and description
- **Configuration change**: Update description
- **Feature addition**: Add note about new capabilities

### For introduction-to-[topic].md

**Structure**:

```markdown
# Introduction to [Topic]

## What is [Topic]?

Conceptual explanation.

## Key Concepts

- Concept 1
- Concept 2

## How It Works

Explanation with diagrams.
```

**Update patterns**:

- **Architecture change**: Update "How It Works" section
- **New concept**: Add to "Key Concepts"
- **Updated explanation**: Revise conceptual sections

## Common Mistakes to Avoid

❌ **Mistake 1: Implementation-Specific Resource Pages**

- Don't create separate pages like "OpenAI Models", "RecursiveChunker Options"
- Use general titles: "Supported Models", "Chunking Options" with implementation sections

❌ **Mistake 2: Adding Setup Instructions**

- Don't add "Setup" or "Installation" sections to reference docs
- Keep resources focused on reference information only
- Link to tutorials for setup instructions

❌ **Mistake 3: Inconsistent Table Structures**

- Don't use different fields for different implementations
- Maintain consistent table structure across all implementations
- Use the same field names and order

❌ **Mistake 4: Marketing Language**

- Don't use promotional language about implementations
- Keep descriptions factual and neutral
- Avoid comparing or ranking implementations

## Best Practice: Reference Documentation Pattern

1. Use general resource title (e.g., "Supported Models", "Chunking Options")
2. Create implementation sections with consistent structure
3. Use tables with identical fields across implementations
4. Keep descriptions brief and factual
5. Link to implementation docs for detailed information

## Special Considerations for Resources

### 1. Maintain Consistency

- Follow existing formatting patterns exactly
- Keep alphabetical ordering where used
- Use consistent terminology
- Match existing note/callout styles

### 2. Accuracy is Critical

- Verify model names are correct
- Ensure version numbers are accurate
- Double-check feature support claims
- Validate links to documentation

### 3. Keep it Reference-Focused

- Resources are for quick lookup, not tutorials
- Keep descriptions concise
- Use tables and lists for scanability
- Link to detailed docs for more info

### 4. Update Related Sections

- If adding a new provider, check all relevant sections
- If updating capabilities, check feature matrices
- If changing terminology, update consistently

## Implementation Guidelines

1. **Apply changes directly**
   - Use edit tools to modify files immediately
   - Make changes section by section in logical order
   - Preserve existing formatting and structure
   - Maintain alphabetical ordering if applicable

2. **Verify changes**
   - Briefly read key sections after editing
   - Check that markdown syntax is valid
   - Ensure tables are properly formatted
   - Verify lists are complete

3. **Report completion**
   - Provide concise summary of changes made
   - List sections that were updated
   - Suggest verifying links and checking related resources
