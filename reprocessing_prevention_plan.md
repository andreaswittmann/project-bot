# Proposal to Prevent Reprocessing of Projects

To prevent the system from reprocessing projects that have already been evaluated, we will implement a tracking mechanism that records the URLs of all processed projects. Before processing a new project from the RSS feed, the system will check against this record.

## Proposed Solution

1.  **Create a Cache File:**
    *   A new file named `processed_projects.log` will be created in the root directory.
    *   This file will store the URLs of all projects that have been successfully processed.

2.  **Update `rss_helper.py`:**
    *   **`load_processed_urls` function:**
        *   A new function will be added to read the `processed_projects.log` file and load the URLs into a set for efficient lookup.
    *   **`fetch_and_process_rss` function:**
        *   The function will be modified to check if a project's URL is already in the set of processed URLs before downloading it.
        *   If the URL is found, the project will be skipped.
        *   After a project is successfully processed and saved, its URL will be appended to `processed_projects.log`.

## Implementation Plan

1.  **Modify `rss_helper.py`:**
    *   Implement the `load_processed_urls` function to read from `processed_projects.log`.
    *   Update `fetch_and_process_rss` to include the check against processed URLs and to write new URLs to the log file.

2.  **Ensure Robustness:**
    *   The system will handle the case where `processed_projects.log` does not exist (e.g., on the first run).

## Mermaid Diagram of the New Workflow

```mermaid
graph TD
    A[main.py] --> B{rss_helper.py};
    B --> C[Load processed_projects.log];
    C --> D{Fetch RSS Feed};
    D --> E{Is Project URL in log?};
    E -->|Yes| F[Skip Project];
    E -->|No| G[Download and Save Project];
    G --> H[Update processed_projects.log];
    H --> I[evaluate_projects.py];