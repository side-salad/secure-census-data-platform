## Upload & Processing Pipeline
### Scope: External Users Only

Only users with external roles (typically union members) can access the upload functionality. Their uploaded census files are processed and stored in two forms
- As raw, unaltered BLOBs
- As cleaned, standardized Excel BLOB
## 1. **Access Control for Upload**
```python
@app.route("/upload", methods=['GET', 'POST'])
@login_required
def upload_file():
    if not ExternalUsers.query.filter_by(email=current_user.id).first():
        return redirect(url_for('home'))
```
**Notes:**
- Route is protected with `@login_required`
- Additional role-check ensures only external users can proceed
## 2. **File Upload and Validation**
```python
file = request.files['file']
if not file or file.filename == '':
    return "No file Uploaded"

file_type = file.filename.split('.')[-1].lower()
df = load_file(file_type, file)
```
**Notes:**
- File must be uploaded via drag and drop
- `load_file()` handles detection and reading of Excel/CSV files into a `pandas.DataFrame`
## 3. **Save Raw (Uncleaned) File to DB**
```python
file.stream.seek(0)
file_bytes = file.read()
unclean_blob(file.filename, label, current_user.id, file_bytes, file_type)
```
**Notes:**
- Raw file is converted to bytes using `.read()` and stored in DB
- `unclean_blob()` stores:
    - Filename
    - Role label (e.g., IUEC)
    - User email
    - Raw byte contents
    - File type
## 4. **Cleaning Pipeline**
### Step 1: **Column Mapping**
```python
column_mapped_df = column_map_final(df.columns, df)
```
- Uses internal mapping logic to align user-submitted columns to standard schema
### Step 2: **Standardization and Deduplication**
```python
column_map_df_cleaned = remove_dupes(clean_items(column_mapped_df))
```
**Notes:**
- `clean_items()` performs:
    - Type normalization
    - Formatting corrections
    - Known column value standardization
- `remove_dupes()` filters out duplicate records by heuristic rules or `pandas.drop_duplicates()`
**Functions Location:** [[Data Cleaning | census_cleaning]] module
## 5. **Convert Cleaned Data to Excel BLOB**
```python
output = io.BytesIO()
column_map_df_cleaned.to_excel(output, index=False, engine='xlsxwriter')
test_bytes = output.getvalue()
```
**Notes:**
- Cleaned DataFrame is written to an in-memory Excel file using `pandas.to_excel()` + `xlsxwriter`
- Output is kept in `BytesIO()` for easy DB upload
## 6. **Save Cleaned File to DB**
```python
clean_blob_excel(file.filename, label, current_user.id, test_bytes, len(df))
```
 **Notes:**
- Saves metadata:
    - Filename
    - Role/Union
    - Email of uploader
    - Row count (for audit/stats)
    - Byte contents of cleaned Excel file
**Function Location:** `dataops/blob.py`

# Frontend

**All front end is handled using the [[Flask Drag and Drop Upload Module | flask-dragdrop]] module.


