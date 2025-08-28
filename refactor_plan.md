# Refactor Plan for evaluate_projects.py

The goal is to refactor `evaluate_projects.py` to process project files from the `./projects` directory instead of the `./emails` directory.

## Todo List

1.  **Rename "email" to "project":**
    *   Change variable names like `email_file` to `project_file`.
    *   Update function names like `process_email_file` to `process_project_file`.
    *   Adjust directory names in variables from `emails_log` to `projects_log`, `emails_accepted` to `projects_accepted`, and `emails_rejected` to `projects_rejected`.
    *   Update help messages in `argparse` to refer to "projects" instead of "emails".

2.  **Update Fluff Filter:**
    *   The current `parse_input_file` function contains logic to remove email-specific headers (From, To, Subject, Date) and footers.
    *   This logic should be removed as the project files from the RSS feed are in Markdown format and do not contain these headers.

3.  **Integrate with `main.py`:**
    *   After a successful run, `main.py` should trigger `evaluate_projects.py`.
    *   This will be achieved by importing `evaluate_projects.main` and calling it at the end of `main.py`.

## Mermaid Diagram of the workflow

```mermaid
graph TD
    A[main.py] -->|fetches new projects| B(./projects/);
    B --> C{evaluate_projects.py};
    C -->|processes files| D(./projects_accepted/);
    C -->|processes files| E(./projects_rejected/);