# Applying a PowerPoint Template to Slidev Slides

## Option 1: Recreate the template as a Slidev theme

Translate the PowerPoint template’s:

- Fonts and colors
- Backgrounds and logos
- Header and footer
- Title and section layouts
- Page numbers
- Required cover and end slides

into CSS, custom layouts, and theme components.

**Pros:** Keeps Slidev’s Markdown, code demos, animations, and live presentation workflow.

**Cons:** Requires manual recreation; PPTX export may not preserve native PowerPoint master layouts.

## Option 2: Export Slidev, then apply the template in PowerPoint

Create the content in Slidev, export to PPTX or PDF, then use PowerPoint to add the conference template’s branding and adjust layouts.

**Pros:** Best compliance with a strict official template.

**Cons:** Exported Slidev content may be less editable, and some layouts or animations may need manual cleanup.

## Option 3: Use PowerPoint for the final deck

Use Slidev only for code demos or prototyping, then reproduce the final slides directly in the provided PowerPoint template.

**Pros:** Maximum compatibility and editability.

**Cons:** Loses much of Slidev’s Markdown and developer-focused workflow.

## Recommendation

If the template is flexible, recreate it in Slidev. If the conference requires the exact `.potx` structure, finish in PowerPoint.
