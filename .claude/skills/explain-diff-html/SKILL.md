---
name: explain-diff-html
description: Use when the user asks for a rich explanation of a code change, diff, branch, or PR. Produces HTML output.
---

<!--
Adapted from Geoffrey Litt's original:
https://gist.github.com/geoffreylitt/a29df1b5f9865506e8952488eac3d524

Modified rather than kept as published -- the output location and the quiz
interaction differ. Every divergence from upstream is listed in the
tedals-monorepo repository at .claude/skills/explain-diff-html/UPSTREAM.md, so
this stays diffable if upstream moves.

Byte-identical copies live in that repo's .claude/skills/ and in both of its
templates/ trees, so every generated project ships it; its
scripts/verify-templates.sh diffs the generated copy against the monorepo one,
so the three cannot drift without a check going red.
-->

# Explain Diff

Please make me a rich, interactive explanation of the specified code change.

It should have these sections:

- Background: Explain the existing system relevant to this change. (You should broadly explore surrounding code for this.) We don't know how much the reader already knows, so include a deep background for beginners (note that it can be skipped if the reader is already familiar), and then a more narrow background directly relevant to the change.
- Intuition: Explain the core intuition for the code change. The focus here is to explain the essence, not the full details. Use concrete examples with toy data. Use figures and diagrams liberally.
- Code: Do a high-level walkthrough of the changes to the code. Group/order the changes in an understandable way.
- Quiz: Come up with five questions that test the reader's knowledge of this PR. This should be medium difficulty, difficult enough that you actually need to understand the substance of the PR to answer them, but not gotchas. The goal is to help the reader make sure that they've actually understood. These should be presented as interactive multiple-choice questions, and when the user clicks, it tells them whether they were correct and gives feedback.

Format:

- Output a single self-contained HTML file which includes CSS and JavaScript. Make the whole thing one long page with section headers and a table of contents. Don't use tabs for the top-level structure. Basic responsive styling so you can view it on a phone is nice too.
- **Emit a complete document, not a fragment.** Open with `<!DOCTYPE html>` and
  `<html lang="en">`; put the `<title>`, `<meta charset="utf-8">`,
  `<meta name="viewport" content="width=device-width, initial-scale=1">` and the
  `<style>` block inside `<head>` … `</head>`; wrap everything else in `<body>` …
  `</body>`; close with `</html>`. Before saving, confirm the last line of the
  file is `</html>`.

  Two of those earn their place rather than being pedantry. Without the charset,
  the em dashes and typographic quotes in your own prose render as mojibake the
  moment the file is opened from disk rather than served. Without the viewport
  meta, the responsive styling asked for above does nothing on a phone — the
  browser lays the page out at desktop width and scales the whole thing down.
- Please write with the clarity and flow of Martin Kleppmann, making it engaging and written in classic style. Transitions between sections should be smooth.
- Some tips on diagrams. Ideally, you should pick a small number of diagram families that can be reused throughout the explanation to explain various cases. Some useful kinds of diagrams:
  - A very simplified version of the UI that the user sees in the app, to explain UI changes.
  - A system diagram showing data flow or communication between components. Make sure to include example data here!
- Don't use ASCII diagrams. Always use simple HTML designs for your diagrams, HTML lists for lists of things, etc.
  - For code blocks, always use `<pre>` tags. If you use a custom styled div instead, it **must** have
    `white-space: pre-wrap` in its CSS, or the browser will collapse all newlines into a single line.
    Before saving the file, scan each code block in the HTML source and confirm its CSS includes
    `white-space: pre` or `pre-wrap`.
- Use callouts for key concepts or definitions, important edge cases, etc.

## Where to write the file

Pick the first of these that applies, creating the directory when it says so:

1. `~/projects/tedals-monorepo/til/` — if that directory already exists. Do not create it.
2. `$XDG_DATA_HOME/til/` — if `XDG_DATA_HOME` is set. Create the `til/` part if needed.
3. `~/.local/share/til/` — create it if needed.
4. `/tmp/` — last resort.

```bash
if [ -d "$HOME/projects/tedals-monorepo/til" ]; then
  til="$HOME/projects/tedals-monorepo/til"
elif [ -n "${XDG_DATA_HOME:-}" ]; then
  til="$XDG_DATA_HOME/til"; mkdir -p "$til"
elif [ -d "$HOME/.local/share" ]; then
  til="$HOME/.local/share/til"; mkdir -p "$til"
else
  til=/tmp
fi
echo "$til"
```

**Name the file `YYYY-MM-DD-explanation-<slug>.html`** — today's date first, always,
so the files stay time-sorted. For example
`~/projects/tedals-monorepo/til/2026-01-12-explanation-quiz-shuffle.html`.

Landing inside a git repository is fine and often the point: these are worth
keeping and worth reading again. Say where you wrote it, and leave committing it
to the reader.

## Quiz mechanics

Each of these was got wrong on a first pass, so they are worth stating.

- **Shuffle the options at render time, on every attempt.** Never emit a fixed
  order. This fixes two problems at once: the correct answer stops occupying the
  same position every time — five questions whose answer is always the first
  option teach nothing — and a retake becomes a genuine second pass rather than a
  memory test on letter positions.
- **Bind each button to its option object, not to its rendered text.** Deciding
  correctness by reading the clicked element's text breaks the moment an option
  contains markup — inline code, an entity, a nested tag — and in a quiz about a
  code change several options usually do. Carry the option itself on the button.
- **Offer a per-question retry, revealed only once that question has been answered
  wrongly.** One wrong answer should not require redoing the set.
- **Offer a whole-quiz retake as well**, which reshuffles every question's options.
- **A retry decrements the answered count.** Otherwise the tally counts attempts
  rather than questions and climbs past the number of questions. It should always
  describe the questions currently counted.
