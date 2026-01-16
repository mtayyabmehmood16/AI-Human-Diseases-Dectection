# CSRF Fix Report

## Issue
Forms were failing with "Bad Request: The CSRF token is missing".
This was caused by:
1. Templates using `{{ csrf_token() }}` directly (raw string output).
2. Templates missing the CSRF token input field entirely in POST forms.

## Fix
All templates have been updated to ensure they contain the correct HTML input tag:
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
```
This was done via automated scripts (`fix_csrf_tokens.py` and `ensure_csrf_tokens.py`) to cover all existing and missing cases.

## Affected Files
### Incorrect Usage (Raw String)
- add_patient.html
- admin.html
- find_form.html
- index.html
- login.html
- match_form.html
- profile.html
- register.html
- search_patients.html
- skin.html
- update_patient.html

### Missing Token (Fixed)
- view_patients.html (Fixes "Delete Patient" error)
- scan.html

## Status
Fixed on 2025-12-15.
All forms in the `templates` directory have been scanned and verified to include the CSRF token.
