# Help System Content Samples - Review

## Overview

This directory contains **5 sample help topics** extracted from USER_GUIDE.md to demonstrate the content structure and quality for the in-app help system.

## Sample Topics Created

### 1. Getting Started: First-Run Wizard (`first-run-wizard.json`)
- **Type:** Overview/Introduction
- **Length:** ~220 words
- **Purpose:** Explain the initial setup process
- **Related topics:** 4 links to detailed wizard steps

### 2. Interface: Status Panel (`status-panel.json`)
- **Type:** Reference/Explanation
- **Length:** ~180 words
- **Purpose:** Explain what the Status Panel shows and what each indicator means
- **Related topics:** 4 links to related interface elements

### 3. Daily Tasks: Turning Projector On (`power-on.json`)
- **Type:** Procedural/How-to
- **Length:** ~210 words
- **Purpose:** Step-by-step guide for the most common daily task
- **Related topics:** 4 links to related operations

### 4. Settings: Connection Settings (`connection-settings.json`)
- **Type:** Configuration/Reference
- **Length:** ~330 words
- **Purpose:** Detailed explanation of all connection configuration options
- **Related topics:** 4 links to related settings and troubleshooting

### 5. Troubleshooting: Cannot Connect (`troubleshoot-connection.json`)
- **Type:** Diagnostic/Problem-solving
- **Length:** ~400 words
- **Purpose:** Systematic troubleshooting steps with decision tree logic
- **Related topics:** 4 links to related diagnostics

## Content Structure (JSON Schema)

Each topic file contains:

```json
{
  "id": "topic-id",                    // Unique identifier (kebab-case)
  "title": "Human-Readable Title",     // Display title
  "category": "category-name",         // One of 6 categories
  "keywords": ["search", "terms"],     // For search engine
  "content": "Markdown text...",       // Main content (supports headings, lists, bold, tips)
  "related_topics": ["id1", "id2"],   // Links to related help topics
  "screenshots": []                    // Array of screenshot filenames (Phase 2)
}
```

## Content Quality Standards

### ✅ What Works Well

- **Concise but complete** - Average 200-350 words per topic
- **Scannable structure** - Clear headings, bullet lists, numbered steps
- **Practical focus** - Real-world scenarios and troubleshooting
- **Progressive disclosure** - Basic info first, details in related topics
- **Helpful tips** - Blockquote tips and warnings where relevant
- **Search-friendly** - Rich keywords covering user terminology

### 📊 Content Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| Average topic length | 200-400 words | ✓ 268 words |
| Markdown formatting | Yes | ✓ Headings, lists, bold, blockquotes |
| Related topics per topic | 3-5 | ✓ 4 average |
| Keywords per topic | 5-10 | ✓ 6-8 average |
| Readability | 8th grade level | ✓ Clear, simple language |

## Next Steps

### Option A: Approve and Extract All Topics
Proceed with extracting all ~68 topics from USER_GUIDE.md using this structure and quality standard.

### Option B: Refine Samples First
Request changes to content structure, length, style, or formatting before full extraction.

### Option C: Add Hebrew Samples
Create Hebrew versions of these 5 topics from USER_GUIDE.he.md to verify RTL content works.

## Sample Topic Preview

See individual JSON files for full content. Here's a quick preview of `power-on.json`:

**Title:** "Turning the Projector On"
**Category:** daily-tasks
**Keywords:** power, on, start, turn on, warm up, boot, startup

**Content excerpt:**
> ## Quick Steps
> 1. Make sure the Status Panel shows **Connected**
> 2. Click the green **Power On** button
> 3. Wait for the projector to warm up (30-60 seconds)
> 4. The Status Panel will update to show **Power: Warming Up**, then **Power: On**
>
> [... continues with troubleshooting, tips, etc.]

---

---

## Hebrew Content Samples (RTL Verification)

Successfully extracted **5 matching Hebrew topics** from USER_GUIDE.he.md:

### Bilingual Content Structure

Each topic exists in both languages with **identical structure**:

| Topic ID | English Title | Hebrew Title (עברית) |
|----------|--------------|---------------------|
| first-run-wizard | First-Run Wizard Overview | סקירת אשף הגדרה ראשונית |
| status-panel | Understanding the Status Panel | הבנת לוח הסטטוס |
| power-on | Turning the Projector On | הפעלת המקרן |
| connection-settings | Connection Settings | הגדרות חיבור |
| troubleshoot-connection | Cannot Connect to Projector | לא ניתן להתחבר למקרן |

### RTL Content Quality

✅ **Hebrew text is properly formatted:**
- Natural Hebrew translations (not machine-translated)
- Right-to-left content flows correctly in JSON
- Technical terms use appropriate Hebrew equivalents
- Markdown formatting preserved (headings, lists, bold)
- Contextual tips and warnings translated accurately

### Sample Hebrew Content Preview

**Topic:** power-on.json (הפעלת המקרן)

```json
{
  "title": "הפעלת המקרן",
  "keywords": ["חשמל", "הפעלה", "התחלה", "הדלקה", "התחממות"],
  "content": "## שלבים מהירים\n\n1. ודא שלוח הסטטוס מציג **Connected**\n2. לחץ על כפתור **Power On** הירוק\n..."
}
```

### Bilingual File Structure

```
docs/help-system-samples/
├── en/                          # English topics
│   ├── first-run-wizard.json
│   ├── status-panel.json
│   ├── power-on.json
│   ├── connection-settings.json
│   └── troubleshoot-connection.json
├── he/                          # Hebrew topics (identical IDs)
│   ├── first-run-wizard.json
│   ├── status-panel.json
│   ├── power-on.json
│   ├── connection-settings.json
│   └── troubleshoot-connection.json
└── SAMPLE_REVIEW.md
```

---

**Created:** 2026-02-13
**Source:** docs/user-guide/USER_GUIDE.md + USER_GUIDE.he.md
**Sample Count:** 10 topics (5 English + 5 Hebrew)
**Location:** docs/help-system-samples/en/ and he/
