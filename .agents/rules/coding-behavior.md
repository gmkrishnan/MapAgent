---
trigger: always_on
---

\---  
name: ai-agent-coding-behavior  
description: the AI coding agent must follow the coding behavior strictly   
version: 1.0.1  
disable-model-invocation: false  
\---

\# 1\. AI Guardrails & Operational Rules

\#\#\# A. Core Behavioral Mandates  
\> \*\*(AI Behavior):\*\* You are strictly forbidden from creating, deleting, or renaming any directory or database model until you have presented the business reasons and architectural justification to the user and received explicit confirmation in chat.   
\> \*\*(Purpose-Driven File Splitting & Structural Clarity):\*\* You are strictly forbidden from dumping unrelated business layers, routing mechanics, database operations, and UI views into a single generic monolithic file. Code must be systematically broken down by architectural concern and responsibility.  
\> \* Every individual App, Module, or Feature must be divided into separate, single-responsibility files inside its specific directory layer (e.g., cleanly separating \`routes.ts\` for endpoints, \`schema.ts\` for database models, \`controller.ts\` for business logic, and \`view.tsx\` for layout components).  
\> \* Do not use arbitrary line counts to force file splits. Split code strictly when moving across architectural layers or distinct domains. If a single component requires extensive internal logic to fulfill its core, cohesive purpose, keep it intact within that file. Prioritize crystal-clear internal organization, clean section formatting, and modular exports.

\#\#\# B. The Four Agent Execution Principles

| Principle | Addresses | Actionable Mechanism |  
| :--- | :--- | :--- |  
| \*\*1. Think Before Coding\*\* | Wrong assumptions, hidden confusion, missing tradeoffs | Stop and clarify ambiguity; present multiple paths explicitly before typing. |  
| \*\*2. Simplicity First\*\* | Overcomplication, bloated abstractions, dead code | Write the absolute minimum code that solves the immediate problem. |  
| \*\*3. Surgical Changes\*\* | Orthogonal edits, touching code you shouldn't | Touch only what you must. Match existing styling perfectly. |  
| \*\*4. Goal-Driven Execution\*\* | Hidden regressions, infinite error loops | Define clear success criteria via a test-first workflow. Limit self-correction loops. |

\#\#\#\# 1\. Think Before Coding (Zero-Assumption Execution)  
Don't assume. Don't hide confusion. Surface tradeoffs. You must slow down and run explicit reasoning:  
\* \*\*State assumptions explicitly:\*\* If a requirement is uncertain, stop and ask the user rather than guessing.  
\* \*\*Present multiple interpretations:\*\* If ambiguity exists in a feature request, present the options rather than silently picking an implementation path.  
\* \*\*Push back when warranted:\*\* If a simpler, more performant, or more secure approach exists to build the feature, surface it before coding.  
\* \*\*Stop when confused:\*\* Name what is unclear immediately and ask for clarification.

\#\#\#\# 2\. Simplicity First (Anti-Overengineering Guardrails)  
Minimum code that solves the problem. Nothing speculative.   
\* Do not build features or capabilities beyond what was explicitly asked.  
\* Do not write generic or predictive abstractions for single-use code.  
\* Do not add "future flexibility" or unrequested configuration toggles.  
\* Do not write error handling or exception traps for impossible, out-of-scope scenarios.  
\* \*\*The Senior Engineer Test:\*\* Code must be highly readable, linear, and stick to standard patterns with minimal logical nesting. If the implementation requires abstract patterns where standard procedural/functional code works, rewrite it using the simplest logical path.

\#\#\#\# 3\. Surgical Changes (Extreme Diff Discipline)  
Touch only what you must. Clean up only your own mess. When editing existing code files:  
\* Do not "improve," reformat, or alter adjacent code, comments, or styling that are orthogonal to your assigned task.  
\* Do not refactor sections that are not explicitly broken.  
\* Match the existing file's coding style perfectly, even if you would personally implement it differently.  
\* If you notice unrelated dead code while working, mention it to the user in chat—do not delete it on your own.  
\* \*\*Handling Orphaned Code:\*\* You must instantly clean up and remove any imports, variables, hooks, or functions that \*your\* specific changes rendered unused. Do not touch pre-existing dead code unless explicitly instructed.  
\* \*\*The Line Trace Test:\*\* Every single line of code modified or added must trace directly back to the user's immediate request.

\#\#\#\# 4\. Goal-Driven Execution (Test-Driven Feedback Loops)  
Transform vague, imperative tasks into verifiable, goal-oriented conditions. 

\* \*\*Task Transformation Matrix:\*\*  
  \* \*Instead of:\* "Add validation" \-\> \*Transform to:\* "Write tests for invalid inputs, then make them pass."  
  \* \*Instead of:\* "Fix the bug" \-\> \*Transform to:\* "Write a test that reproduces the bug, then make it pass."  
  \* \*Instead of:\* "Refactor Component X" \-\> \*Transform to:\* "Ensure all existing tests pass flawlessly before and after the modification."

\* \*\*Multi-Step Execution Planning:\*\* For any multi-step task, you must output a brief sequential plan before beginning, structured like this:  
  1\. \`\[Step Title/Goal\]\` \-\> \*verify:\* \`\[Specific Automated Check/Test Condition\]\`  
  2\. \`\[Step Title/Goal\]\` \-\> \*verify:\* \`\[Specific Automated Check/Test Condition\]\`

\* \*\*Circuit Breaker Rule:\*\* If an automated check, test, or compilation step fails 3 times consecutively during your execution loop, you must stop immediately. Do not keep changing code blindly. Present the current diff, the error logs, and ask the user for guidance.