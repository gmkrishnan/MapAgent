---
trigger: always_on
---

---
name: workspace-directory-rules
description: Enforces the absolute physical root path restrictions and subfolder placement for backend and frontend code separation.
version: 1.0.0
disable-model-invocation: false
---

# Workspace Directory & Repository Rules

## 1. AI Guardrails & Operational Path Restraints

### A. Target Path Restrictions
> **CRITICAL PATH LOCKDOWN:** You are strictly confined to reading, writing, updating, or generating code within the designated working folder root. You are forbidden from initializing code blocks outside of this directory container.
> * **Absolute Target Working Root:** `D:\Building\healthcare\swastha\prototype\v1-swastha-prototype\apps`

### B. Repository Segregation Matrix
Every code artifact, layout view, or logic controller must be systematically triaged into its specific architectural codebase folder:

*   **Backend Code:** All API routes, endpoint handlers, database schemas, utility middleware, and server logic must reside exclusively inside the `backend/` directory path:
    `D:\Building\healthcare\swastha\prototype\v1-swastha-prototype\apps\backend/`
*   **Frontend Code:** All UI views, presentation layouts, state components, styling assets, and client runtime hooks must reside exclusively inside the `frontend/` directory path:
    `D:\Building\healthcare\swastha\prototype\v1-swastha-prototype\apps\frontend/`

### C. apps/ Root Permission Lock

> **CRITICAL:** The `apps/` directory root at `D:\Building\healthcare\swastha\prototype\v1-swastha-prototype\apps` is strictly locked.
> You are forbidden from creating, writing, or placing any file directly inside `apps/` root under any circumstance.
> **Only Exception:** If the user grants explicit one-time permission in chat for a specific named file, you may create only that exact file. After completing it, the lock resets immediately — no carryover permission applies to any future file.
> Before acting on any such permission, you must confirm the exact filename with the user.

*   **Backend Code:** All API routes, endpoint handlers, database schemas, utility middleware, and server logic must reside exclusively inside the `backend/` directory path:
    `D:\Building\healthcare\swastha\prototype\v1-swastha-prototype\apps\backend/`
*   **Frontend Code:** All UI views, presentation layouts, state components, styling assets, and client runtime hooks must reside exclusively inside the `frontend/` directory path:
    `D:\Building\healthcare\swastha\prototype\v1-swastha-prototype\apps\frontend/`
---

## 2. Directory Cleanliness Guardrails

### A. Root Pollution Prevention
*   **Zero Loose Files:** You are strictly forbidden from creating loose code files, temporary logic files, or isolated modules directly in the root of the `apps/` working folder. 
*   **Explicit Exceptions:** The only files allowed to sit at the absolute root level are standard global documentation and version control configurations:
    *   `.gitignore`
    *   `README.md`

### B. Execution Compliance Check
Before executing any file-write, directory creation, or change diff, you must run an automated check to verify that the file path traces perfectly inside either the `backend/` or `frontend/` directories. If a requested path breaches the root file constraint, stop execution immediately and prompt the user to specify the correct subfolder location.


### C. Module & Feature Directory Decomposition Rule

> **CRITICAL (Structural Mandate):** Every app, module, plugin, or feature must be broken down into its own dedicated subfolder. You are strictly forbidden from placing multiple unrelated concerns or features inside a single flat directory.

#### Decomposition Rules:

* Every distinct **app, module, plugin, or feature** must have its own dedicated subfolder.
* **Inside each subfolder**, code must be split by architectural concern into single-responsibility files:
  - `models.py` → Database schema / ORM models only
  - `routes.py` → API endpoint definitions only
  - `services.py` → Business logic only
  - `schemas.py` → Request/response schemas only
* **No flat dumping:** You are forbidden from mixing route handlers, business logic, database models, and schemas into a single file regardless of file size.
* **No speculative folders:** Only create a subfolder when a real feature or module requires it. Do not pre-create empty placeholder directories.