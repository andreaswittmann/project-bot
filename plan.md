# Plan: Change Cron Schedule Field to Dropdown with Presets

## Overview
The task is to modify the Scheduler Manager UI in the Edit Schedule and Create New Schedule dialog. Currently, the Cron Schedule field is a text input. We need to change it to a dropdown box pre-filled with 10 relevant cron schedule presets.

## Current State Analysis
- The form is in `frontend/src/components/ScheduleFormEnhanced.vue`
- Cron Schedule field is currently an `<input type="text">` with placeholder "0 9-17 * * 1-5"
- Includes basic validation on blur
- Has help text with examples

## Implemented Changes

### 1. Defined 10 Cron Presets
The following presets are included in the dropdown:

1. **Run 4x per day on weekdays** - `0 9,12,15,18 * * 1-5` (9am, 12pm, 3pm, 6pm Mon-Fri)
2. **Run 1x per day on weekends** - `0 10 * * 0,6` (10am Sat-Sun)
3. **Run 2x every Monday** - `0 9,15 * * 1` (9am, 3pm Mondays)
4. **Run 15 min past every 2 hours** - `15 */2 * * *` (every 2 hours at :15)
5. **Run every hour** - `0 * * * *` (top of every hour)
6. **Run daily at midnight** - `0 0 * * *` (12:00 AM every day)
7. **Run weekly on Sunday** - `0 0 * * 0` (midnight Sundays)
8. **Run monthly on the 1st** - `0 0 1 * *` (midnight 1st of month)
9. **Run every 30 minutes** - `*/30 * * * *` (every half hour)
10. **Don't run at all** - `0 0 31 2 *` (Feb 31st - never runs)

### 2. UI Changes to ScheduleFormEnhanced.vue ✅
- Used an `<input>` element with `<datalist>` for editable dropdown functionality
- Added `<option>` elements for each preset in the datalist (value=cron expression, label=description)
- Input allows both selection from presets and custom cron expression entry
- Updated validation trigger from `@blur` to `@input`
- Added placeholder and help text to guide users

### 3. Form Logic Updates ✅
- Updated default `cron_schedule` to first preset: `0 9,12,15,18 * * 1-5`
- Updated fallback in `initializeForm` to use the same default
- Maintained existing validation logic (basic cron format check)
- Kept the validation display (success/error messages)

### 4. Testing ✅
- Verified dropdown renders correctly with all 10 options
- Confirmed build succeeds without errors
- Frontend dev server runs successfully
- Form structure and validation logic intact

## Status: COMPLETED
All changes have been implemented and tested. The Cron Schedule field now displays as a user-friendly dropdown with 10 preset options instead of a text input requiring manual cron expression entry.