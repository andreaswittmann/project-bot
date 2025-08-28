# Refactor Implementation Todo List

## Phase 1: File Cleanup and Organization 🧹

### 1.1 Remove Obsolete Planning Documents ✅
- [ ] **Delete obsolete planning files**
  - [ ] Remove [`refactor_plan.md`](refactor_plan.md) - Original refactor is complete
  - [ ] Remove [`reprocessing_prevention_plan.md`](reprocessing_prevention_plan.md) - Feature already implemented
  - [ ] Remove [`plan.md`](plan.md) - Superseded by current implementation
  - [ ] Remove [`git_setup_todo.md`](git_setup_todo.md) - One-time setup, no longer needed

### 1.2 Consolidate Documentation ✅
- [ ] **Merge dashboard documentation**
  - [ ] Review content in [`dashboard_plan.md`](dashboard_plan.md) and [`dashboard_architecture.md`](dashboard_architecture.md)
  - [ ] Extract relevant content and merge into [`dashboard_todo.md`](dashboard_todo.md)
  - [ ] Remove redundant files after consolidation
- [ ] **Update main documentation**
  - [ ] Review and update [`README.md`](README.md) project structure section
  - [ ] Ensure all current features are documented
  - [ ] Remove references to deleted planning files

## Phase 2: Code Structure Improvements 🏗️

### 2.1 Extract Constants and Remove Hardcoded Values ✅
- [ ] **Create constants module**
  - [ ] Create `src/constants.py` file
  - [ ] Move hardcoded values to constants:
    ```python
    # HTTP request constants
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8"
    }
    
    # HTML parsing constants
    HTML_LABELS = ["Start", "Von", "Auslastung", "Eingestellt", "Ansprechpartner:", ...]
    
    # File system constants
    LOG_DIR = 'projects_log'
    PROCESSED_LOG_FILE = 'processed_projects.log'
    ```
- [ ] **Remove hardcoded URL from [`parse_html.py:6`](parse_html.py:6)**
  - [ ] Delete the unused `URL` constant
  - [ ] Verify no other code references this constant

### 2.2 Decompose Large Functions ✅
- [ ] **Refactor [`evaluate_projects.py:245`](evaluate_projects.py:245) - `process_project_file()`**
  - [ ] Extract logging setup: `setup_project_logging()`
  - [ ] Extract project loading: `load_and_validate_project()`
  - [ ] Extract evaluation pipeline: `evaluate_project_pipeline()`
  - [ ] Extract result handling: `handle_project_result()`
  - [ ] Update main function to use decomposed functions

- [ ] **Refactor [`parse_html.py:129`](parse_html.py:129) - `parse_project()`**
  - [ ] Extract HTML fetching: `fetch_project_html(url: str) -> str`
  - [ ] Extract data parsing: `extract_project_data(html: str) -> Dict`
  - [ ] Update `parse_project()` to orchestrate these functions

### 2.3 Improve Error Handling ✅
- [ ] **Create error handling utilities**
  - [ ] Create `src/exceptions.py` with custom exception classes
  - [ ] Create `src/error_handlers.py` with standardized error handling
  - [ ] Replace inconsistent try/except blocks with standardized handlers

## Phase 3: Code Quality Improvements 🔧

### 3.1 Clean Up Imports ✅
- [ ] **Review and clean [`parse_html.py:1`](parse_html.py:1) imports**
  - [ ] Remove unused imports: `json`, `math`, `time` (verify usage first)
  - [ ] Organize imports by standard library, third-party, local
  - [ ] Use specific imports where possible

- [ ] **Review and clean [`evaluate_projects.py:1-11`](evaluate_projects.py:1-11) imports**
  - [ ] Verify all imports are used
  - [ ] Group and sort imports logically
  - [ ] Add type imports for better type hints

### 3.2 Add Comprehensive Documentation ✅
- [ ] **Document [`evaluate_projects.py`](evaluate_projects.py) functions**
  - [ ] Add docstrings to [`pre_evaluate_project()`](evaluate_projects.py:92)
  - [ ] Add docstrings to [`analyze_with_llm()`](evaluate_projects.py:150)
  - [ ] Add docstrings to [`process_project_file()`](evaluate_projects.py:245)
  - [ ] Add parameter and return type documentation

- [ ] **Document [`parse_html.py`](parse_html.py) functions**
  - [ ] Add docstrings to [`parse_project()`](parse_html.py:129)
  - [ ] Add docstrings to [`extract_keywords()`](parse_html.py:111)
  - [ ] Add docstrings to [`get_heading_block()`](parse_html.py:56)

- [ ] **Document [`rss_helper.py`](rss_helper.py) functions**
  - [ ] Add docstrings to all public functions
  - [ ] Document the RSS processing workflow

### 3.3 Add Type Annotations ✅
- [ ] **Add type hints to [`evaluate_projects.py`](evaluate_projects.py)**
  - [ ] Add type imports: `from typing import Dict, List, Optional, Tuple, Callable`
  - [ ] Add return type annotations to all functions
  - [ ] Add parameter type annotations

- [ ] **Add type hints to [`parse_html.py`](parse_html.py)**
  - [ ] Import required types from `typing` and `bs4`
  - [ ] Add type annotations to all functions
  - [ ] Specify `BeautifulSoup` and `Tag` types where used

### 3.4 Add Input Validation ✅
- [ ] **Add validation to critical functions**
  - [ ] Validate inputs in [`pre_evaluate_project()`](evaluate_projects.py:92)
  - [ ] Validate configuration in [`load_config()`](evaluate_projects.py:25)
  - [ ] Add URL validation in [`parse_project()`](parse_html.py:129)

## Phase 4: Dashboard Code Review ✅

### 4.1 Review Dashboard Scripts ✅
- [ ] **Analyze [`dashboard/generate_dashboard_data.py`](dashboard/generate_dashboard_data.py)**
  - [ ] Check for code quality issues
  - [ ] Verify error handling consistency
  - [ ] Add missing type hints and documentation
  - [ ] Extract magic values to constants

## Phase 5: Configuration Improvements ✅

### 5.1 Centralize Configuration Management ✅
- [ ] **Create configuration utilities**
  - [ ] Create `src/config.py` with `AppConfig` class
  - [ ] Add configuration validation methods
  - [ ] Centralize all configuration access through this class
  - [ ] Update all modules to use centralized configuration

## Testing and Validation (Optional) 🧪

### 6.1 Add Basic Tests ✅
- [ ] **Create test structure**
  - [ ] Create `tests/` directory
  - [ ] Add `conftest.py` for test configuration
  - [ ] Create test files for critical functions

- [ ] **Write tests for core functions**
  - [ ] Test [`pre_evaluate_project()`](evaluate_projects.py:92) with various inputs
  - [ ] Test configuration loading and validation
  - [ ] Test HTML parsing edge cases

## Implementation Checklist

### Quick Wins (1-2 hours) ✅
- [ ] Delete obsolete planning documents
- [ ] Remove hardcoded URL from [`parse_html.py`](parse_html.py)
- [ ] Clean up unused imports
- [ ] Add basic docstrings to main functions

### Medium Effort (3-4 hours) ✅
- [ ] Decompose large functions into smaller ones
- [ ] Add comprehensive type annotations
- [ ] Standardize error handling patterns
- [ ] Add input validation to critical functions

### Larger Refactoring (Optional, 4+ hours) ✅
- [ ] Create proper module structure with `src/` directory
- [ ] Centralize configuration management
- [ ] Add comprehensive test suite

## Validation Steps ✅
After each phase:
- [ ] Run all scripts to ensure functionality is preserved
- [ ] Test with sample data to verify behavior
- [ ] Check that all imports resolve correctly
- [ ] Verify configuration loading still works

## Success Criteria ✅
- [ ] **File Count:** Reduced by 4-5 obsolete documents
- [ ] **Function Length:** No functions over 50 lines
- [ ] **Documentation:** All public functions have docstrings
- [ ] **Type Safety:** Critical functions have type annotations
- [ ] **Error Handling:** Consistent error handling patterns
- [ ] **Maintainability:** Code is easier to understand and modify

## Breaking Changes Tracking ⚠️
Document any changes that might affect existing usage:
- [ ] Module import paths (if `src/` structure is implemented)
- [ ] Function signatures (minimal changes expected)
- [ ] Configuration file validation (should be backward compatible)

---

**Priority Order:** Complete Phase 1 → Phase 2 → Phase 3 → Consider Phase 4-5 based on time/effort requirements.

Each checkbox can be completed independently, allowing for incremental progress and testing at each step.