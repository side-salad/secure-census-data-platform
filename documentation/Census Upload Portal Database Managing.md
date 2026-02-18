## `/dataops` — Data Operations Utilities
The `/dataops` package contains **database models** and **helper functions** for storing and manipulating:
- Cleaned and uncleaned census data
- Structured records
- Internal/external user whitelists
- Admin logs
It supports both blob (binary file) storage and structured row-level inserts.
## Package Structure
```text
/dataops
│
├── __init__.py          → Consolidates internal imports
├── models.py            → All SQLAlchemy DB models
├── blob.py              → File blob (BLOB) insertion logic
└── loader.py            → Cleaned structured inserts + admin log recording
```
## `models.py` (SQLAlchemy Models)
Defines the full schema of the database used in your Flask app.
### Main Tables
#### `Cleaned`
Structured cleaned records for downstream analysis or export. Not used in this app specifically but can be reformatted for later use. Has simple example column names.
#### `BlobOriginal` / `BlobCleaned`
Stores uploaded census files as raw binary (BLOBs).
- `BlobOriginal`: raw upload
- `BlobCleaned`: cleaned Excel output
Each contains:
- `filename`, `email`, `union`
- `file_type`, `uploaded_at`
- `file_blob` (actual bytes)
- `rowcount` (only in `BlobCleaned`)
#### `InternalUsers` / `ExternalUsers`
Used for login whitelisting. Populated through admin dashboard.
#### `UserLog`
Tracks actions (e.g., download, preview) performed by internal users.
## `blob.py` — BLOB Upload Helpers
Encapsulates logic for saving census files to the database:
```python
def unclean_blob(filename, union, email, blob_data, file_type)
```
- Saves the unprocessed file into `BlobOriginal`
```python
def clean_blob_excel(filename, union, email, excel_blob: bytes, rowcount)
```
- Stores the cleaned output as `.xlsx` in `BlobCleaned`
- Adjusts filename extension automatically
- Records row count of cleaned data
These functions are used by:
- Manual uploads (external interface)
- Automated uploads (`sftp_watcher.py`)
## `loader.py` — Structured Inserts & Logs
Handles structured data inserts after the cleaning pipeline.
```python
def insert_cleaned_data(df)
```
- Converts DataFrame to records and bulk-inserts into `Cleaned` table
```python
def insert_log(user, file, action)
```
- Adds an entry to `UserLog` when an internal user performs a key action
- Used by preview and download routes for observability
## `__init__.py`
Simpy exposes submodules:
```python
from .models import *
from .blob import *
from .loader import *
```
This allows simplified access throughout the app:
```python
from dataops import clean_blob_excel, insert_cleaned_data, UserLog
```
## Example Usage in App
```python
# After a file is cleaned and deduplicated
clean_blob_excel(filename, union, email, cleaned_bytes, len(df))

# Log the user action
insert_log(current_user.id, filename, 'preview')

# Insert structured records from DataFrame
insert_cleaned_data(cleaned_df)
```