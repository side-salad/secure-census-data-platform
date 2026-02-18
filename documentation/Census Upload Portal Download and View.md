## Download & View — Internal Users Only
### **Internal Dashboard (`/internal/files`)**
#### What It Does:
- Displays a table of all cleaned census files uploaded by external users.
- Visible only to internal users (role = `'internal'`).
- Shows metadata like:
    - Filename
    - Uploading user's email
    - Associated union
    - Upload timestamp
    - Row count of the cleaned file
#### Access Control:
```python
if current_user.role != 'internal':
    return redirect(url_for('home'))
```
#### Query & Render Logic:
```python
files = BlobCleaned.query.with_entities(
    BlobCleaned.id, BlobCleaned.filename, BlobCleaned.union,
    BlobCleaned.email, BlobCleaned.uploaded_at, BlobCleaned.rowcount
).order_by(BlobCleaned.uploaded_at.desc()).all()
```
#### Rendered via:
```python
return render_template("inthome.html", files=files_dict)
```
Each file is displayed with a download button linking to `/download/<file_id>`.
### **File Download Route (`/download/<file_id>`)**
#### What It Does:
- Streams a cleaned census Excel file from the database to the user’s device.
- File is fetched by ID and returned as an attachment.
#### Role Check:
```python
if current_user.role != "internal":
    return redirect(url_for('home'))
```
#### File Fetch & Response:
```python
file = BlobCleaned.query.get(file_id)
if file:
    return send_file(
        io.BytesIO(file.file_blob),
        as_attachment=True,
        download_name=file.filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
```
If the `file_id` is invalid, the route returns `"File not found"`.

### **File View Route (`/preview/<int:file_id>`)**
#### What It Does:
- Gives a 10 row preview of cleaned census files 
- File is fetched by ID and returned as a viewable table in browser
#### Role Check:
```python
if current_user.role != "internal":
    return redirect(url_for('home'))
```
#### File Fetch & Response:
```python
if not file:
	return "File not found", 404
try:
	excel_data = io.BytesIO(file.file_blob)
	df = pd.read_excel(excel_data).head(10)
	table = df.to_html(classes='preview_table', index=False)
	insert_log(current_user.id, file.filename, 'preview')
	return table
except Exception:
	return "File not found", 404
```
If the `file_id` is invalid, the route returns `"File not found"`.

### **Battery Bar Route (`/update-stage/<int:file_id>`)**
#### What It Does:
- POST only route for updating status on a specific census
	- Status positions in order include: uploaded, processing(cleaning, parsing, etc.), and completed
- Status positions are stored in database in `BlobCleaned` table
#### Role Check:
```python
if current_user.role != "internal":
    return redirect(url_for('home'))
```
#### File Fetch & Response:
```python
def update_file_stage(file_id):
    if current_user.role != "internal":
        return redirect(url_for('home'))
    data = request.get_json()
    new_status = data.get('stage')
    file_record = BlobCleaned.query.get_or_404(file_id)
    file_record.status = new_status
    db.session.commit()
    return jsonify({'success': True, 'status': file_record.status})
```
If the `file_record` is invalid, the route returns `404` error for specific file ID attempting to be altered.

### **Frontend Behavior (inthome.html and viewmode.js)**

## 1. Table Rendering and Interaction
#### Structure
Each file is rendered into a row within a `<table>` like this:
```html
<tr>
  <td>filename.xlsx</td>
  <td>Union Name</td>
  <td>user@email.com</td>
  <td>2025-07-15 10:30</td>
  <td>1,024</td>
  <td>
    <div class="dropdown">
      <button class="dropdown-toggle">. . .</button>
      <div class="dropdown-menu">
        <a onclick="openModal('download', '123')">Download</a>
        <a onclick="openModal('view', '123')">View</a>
      </div>
    </div>
  </td>
</tr>
```
Each row contains:
- Metadata (filename, union, email, timestamp, row count)
- A dropdown menu with action buttons for Download and View (hooked to modals)
## 2. Filtering by Union or Email
#### Inputs:
```html
<input id="searchInput" onkeyup="filterFilename()">
<input id="searchEmail" onkeyup="filterEmail()">
```
These use simple `keyup` listeners to dynamically hide rows that don’t match:
```js
function filterFilename() {
  const input = document.getElementById("searchInput").value.toLowerCase();
  const rows = document.querySelectorAll("#fileTable tbody tr");
  rows.forEach(row => {
    const union = row.children[1].textContent.toLowerCase();
    row.style.display = union.includes(input) ? "" : "none";
  });
}
```
This allows the table to be filtered without refreshing the page.
## 3. Sorting by Upload Date
The upload date column is clickable:
```html
<th onclick="sortTableByDate()">Upload Date <span id="sortArrow">▲</span></th>
```
Clicking toggles between ascending/descending. The implementation uses the `Date()` constructor to compare values:
```js
function sortTableByDate() {
  const rows = Array.from(document.querySelectorAll("#fileTable tbody tr"));
  rows.sort((a, b) => {
    const dateA = new Date(a.children[3].textContent);
    const dateB = new Date(b.children[3].textContent);
    return ascending ? dateA - dateB : dateB - dateA;
  });
  rows.forEach(row => tbody.appendChild(row));
  ascending = !ascending;
}
```
## 4. Download Confirmation Modal
When the user clicks “Download”, a **confirmation modal** appears:
```js
function openModal(action, fileId) {
  if (action === "download") {
    const modal = document.getElementById("modalDownload");
    modal.style.display = "flex";
    document.getElementById("submitRow").onclick = () => {
      window.location.href = `/download/${fileId}`;
    };
  }
}
```
This adds a "Are you sure?" step before downloading large census files.
##  5. Preview Table Modal
Clicking “View” opens a scrollable preview modal. It fetches the first 10 rows of the Excel file:
```js
function openModal(action, fileId) {
  if (action === "view") {
    const modal = document.getElementById("modalPreview");
    modal.style.display = "flex";
    fetch(`/preview/${fileId}`)
      .then(res => res.text())
      .then(html => {
        document.getElementById("previewTable").innerHTML = html;
      });
  }
}
```
The modal displays the `df.head(10)` preview generated server-side using `pandas.to_html()`, styled with `.preview_table`.
##  6. Status Battery Bar
Clicking the battery bar on the table triggers JavaScript and opens modal:
```html
<td><div class="battery" data-id="{{ file.id }}" data-stage="{{ file.status }}" onclick="openStatusModal(this.dataset.id, this.dataset.stage)"></div></td>
```
Rendering the battery and it's stages is done purely in JS and CSS with custom stage labeling:
```javascript
function renderBattery(batt) {
    const stage = parseInt(batt.dataset.stage);
    batt.innerHTML = '';
    for (let i = 0; i < 3; i++) {
        const section = document.createElement('div');
        if (i <= stage) section.classList.add(`stage-${i}`);
        batt.appendChild(section);
    }
}
```
```css
.stage-0 { background-color: #a1adb9; }
.stage-1 { background-color: #5477a0; }
.stage-2 { background-color: #0E56A7; }
```

Submitting changes to database is done by fetching id of database row for use in flask route:
``` javascript
function submitStageChange() {
    const modal = document.getElementById('modalStatus');
    const id = modal.dataset.processId;
    const stage = document.getElementById('stageSelector').value;
    fetch(`/update-stage/${id}`, {
        method: 'POST',
        body: JSON.stringify({ stage }),
        headers: { 'Content-Type': 'application/json' }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            const battery = document.querySelector(`.battery[data-id='${id}']`);
            battery.dataset.stage = data.status;
            renderBattery(battery);
        }
        modal.style.display = 'none';
    });
}
```