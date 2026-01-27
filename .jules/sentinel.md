## 2026-01-27 - HTML Injection via aiogram ParseMode.HTML
**Vulnerability:** User input was directly interpolated into messages while `ParseMode.HTML` was enabled globally, allowing HTML injection.
**Learning:** When using `aiogram` with `ParseMode.HTML`, all user input must be escaped using `html.escape`. Validation alone is insufficient if it allows characters like `<` or `>`.
**Prevention:** Always use `html.escape` for any user-controlled data before string interpolation in messages.
