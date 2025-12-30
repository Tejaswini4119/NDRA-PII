# NSRL Forbidden Patterns

To maintain safety and simplicity, the following are strictly disallowed:

1.  **Turing Completeness**: No recursion, no `while` loops, no variable declaration/assignment.
2.  **Code Injection**: No `eval()`, `exec()`, or embedding of script snippets (Python/JS/Lua).
3.  **Complex Regex**: Regular expressions (if allowed) must be bounded (e.g., ReDOS safe). *Recommendation: Use string matching primitives instead.*
4.  **Dynamic Imports**: No loading other rules at runtime. All rules are static.
5.  **Ambiguous Types**: Values must be explicitly typed (String, Number, Boolean, List).