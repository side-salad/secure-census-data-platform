## SFTP Watcher
The `sftp_watcher.py` module continuously monitors a shared SFTP directory for newly uploaded census files. Mirrors the cleaning and uploading process in actual web app

This service runs **in a background thread** and operates entirely server-side.
### What It Does
- Watches a configured SFTP directory using a polling-based filesystem observer.
- Data is loaded and cleaned via the [[Data Cleaning | census_cleaning]] module and stored via the [[Census Upload Portal Database Managing | /dataops]] functions
### Core Components
#### 1. `start_observer()`
Starts a polling observer and attaches a handler:
```python
observer.schedule(event_handler, WATCH_PATH, recursive=True)
observer.start()
```
This function is invoked in the Flask entry point via:
```python
watcher_thread = threading.Thread(target=start_observer, daemon=True)
watcher_thread.start()
```
This ensures the watcher runs independently in the background of your Flask app.
#### 2. `UploadHandler.on_created(event)`
Triggered when a new file appears in the watch directory. It:
- Ignores directories and temp/dotfiles
- Calls `process_file()` for supported file types:
```python
if filename.startswith(".") or not filename.endswith(('.csv', '.xlsx', '.xls', '.txt')):
    return
```
#### 3. `process_file(path, email="sftp")`
This is the main pipeline for SFTP-uploaded files. It mimics the manual upload and cleaning flow used on the web app.
Steps:
1. **Load File**
    ```python
    df = load_file(file_type, path)
    ```
2. **Upload Raw File (Uncleaned)**
    ```python
    unclean_blob(filename, label, email, file_bytes, file_type)
    ```
3. **Clean File**
    ```python
    column_mapped_df = column_map_final(df.columns, df)
    cleaned_df = remove_dupes(clean_items(column_mapped_df))
    ```
4. **Upload Cleaned File**
    ```python
    clean_blob_excel(filename, label, email, cleaned_bytes, len(df))
    ```
Files are saved under the `label` derived from the folder the file was dropped into:
```python
label = os.path.basename(os.path.dirname(path))
```
### Example Flow
1. A `.xlsx` file is uploaded via SFTP into `/secure/filepath`.
2. `UploadHandler` detects the new file and triggers `process_file()`.
3. File is cleaned and two database records are created:
    - One in `BlobUncleaned` (raw BLOB)
    - One in `BlobCleaned` (Excel BLOB, deduplicated, mapped)
### Internal Access & Visibility
SFTP-uploaded files are **tagged with `email='sftp'`** in the database. They appear in the **Admin page's SFTP Users table** for internal review.
```python
BlobCleaned.query.filter(BlobCleaned.email == 'sftp')
```