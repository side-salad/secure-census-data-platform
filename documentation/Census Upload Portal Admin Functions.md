# Census Upload Portal Admin Functions
The Admin Functions page is accessible to **internal Union One members** only and provides a secure interface to **add, edit, or delete**:
- Internal Admins (users with `@unionone.com` emails)
- External Union Members (portal users associated with a union)
- View-only SFTP Uploads
All actions are gated behind login and role-based access control (`current_user.role == 'internal'`).
## **Admin Management**
#### Add Admin (`/add_admin`)
- Adds a new admin user to the `InternalUsers` table.
- Email must end in `@unionone.com`.
- Fails if the email already exists.
```python
@app.route("/add_admin", methods=["POST"])
def add_admin():
    if '@unionone.com' not in data['email']:
        return jsonify(
        success=False, message="Email must end in @unionone.com"
        ), 400
```
#### Edit Admin (`/edit_admin-members`)
- Allows updating first name, last name, and email.
- Prevents overwriting an existing user’s email.
```python
if original_email.strip().lower() != updated_email.strip().lower():
    bad = InternalUsers.query.filter(...).first()
    if bad:
        return jsonify(success=False, message="Email already exists"), 400
```
#### Delete Admin (`/delete_admin-members`)
- Deletes a user by matching `original_email` (case-insensitive, whitespace-trimmed).
- Returns success/failure JSON response.

## **Union Member Management**
Union users are managed similarly to admins but stored in a separate `ExternalUsers` table. An extra `union` field is required.
#### Add Union Member (`/add_union_members`)
```python
new = ExternalUsers(..., union=data['union'], ...)
```
#### Edit Union Member (`/edit_union-members`)
- Uses the same email validation logic.
- Updates all four fields: name, email, and union.
#### Delete Union Member (`/delete_union-members`)
- Follows the same pattern as admin deletion.
- Uses `original_email` as primary lookup key.
## **SFTP Users (View Only)**
- Pulled from `BlobCleaned` where `email == 'sftp'`
- Displayed as metadata in a read-only table.
```python
sftp_files = BlobCleaned.query.filter(BlobCleaned.email == 'sftp')...
```
## **Frontend Behavior (admin.html and filter.js)**
The admin page is split into 3 table sections:
1. **Admins**
2. **Union Members**
3. **SFTP Users**
Each section:
- Is paginated (7 rows per page)
- Can be filtered by union/email
- Has an **Add Row** trigger and **Edit** pencil icon
All modal interactions route to the backend via `fetch()` and expect JSON:
```js
fetch(`/edit_${tableType}`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload)
})
```
### 1. Table Filtering, Sorting, and Pagination
Each `.table-section` is initialized with:
```js
setupTableSection(section)
```
This function enables:
- **Filtering by email or union** using `.searchInput` and `.searchEmail`
- **Sorting by upload date** via a clickable sort arrow
- **Paginated rendering** (`rowsPerPage = 7`)
#### Filtering Example:
```js
function filterTable() {
  const unionVal = searchInput?.value.toLowerCase() || "";
  const emailVal = searchEmail?.value.toLowerCase() || "";
  rows.forEach(row => {
    const union = row.children[1].textContent.toLowerCase();
    const email = row.children[2].textContent.toLowerCase();
    row.style.display = (union.includes(unionVal) && email.includes(emailVal)) ? "" : "none";
  });
}
```
Filtering works independently per table. Filtering inputs are optional (not all sections use both inputs.)
### 2. Modal System (Add/Edit/Delete)
Each row interaction (add or edit) opens a **floating modal**:
```html
<div class="modal-backdrop" id="modalBackdrop">
  <div class="modal-form">
    <h3 id="modalTitle"></h3>
    <div id="modalFields"></div>
    <button id="submitRow">Submit</button>
    <button id="cancelModal">Cancel</button>
    <button id="deleteRow">Delete</button>
  </div>
</div>
```
#### Opening the Modal
- Clicking a "+" row opens an **Add Modal**:
```js
document.querySelectorAll('.add-row-trigger').forEach(row => {
  row.addEventListener('click', () => {
    modal.dataset.mode = "add";
    modalFields.innerHTML = getModalFields(tableType);
    ...
  });
});
```
- Clicking the ✏️ icon opens an **Edit Modal** with prefilled values from the row:
```js
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('edit-icon')) {
    ...
    const cells = row.querySelectorAll('td');
    modalFields.innerHTML = getModalFields(tableType, cells);
  }
});
```
#### Modal Field Generator
Dynamic form generation is handled by:
```js
function getModalFields(tableType, cells = []) {
  ...
  if (tableType === "union-members") {
    html += `<input id="union" value="${cells[4]?.textContent.trim()}" />`
  }
}
```
This makes the modal reusable for both Admins and Union Members.
### 3. Submit and Delete Logic
#### Submitting a Form
- Validates required fields
- Sends `POST` request to backend route (`/add_admin`, `/edit_union-members`, etc.)
```js
fetch(endpoint, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload)
})
```
If validation fails server-side (e.g. duplicate email), errors are displayed inline:
```js
const error = document.createElement("div");
error.textContent = data.message || "An error occurred.";
emailInput.insertAdjacentElement("afterend", error);
```
#### Deleting a User
Triggered from the same modal during **edit** mode. Sends `POST` with only the `original_email`.
```js
fetch(`/delete_${tableType}`, {
  method: "POST",
  body: JSON.stringify({ original_email: email })
})
```
### 4. Auto-Reload on Success
All submit/delete actions finish with:
```js
location.reload(true);
```
This ensures fresh data is re-rendered after any update.
### Summary of Table Types

| Table Type      | Backend Route Prefix                      | Fields Required                             |
| --------------- | ----------------------------------------- | ------------------------------------------- |
| `admin-members` | `add_admin`, `edit_admin-members`         | `first_name`, `last_name`, `email`          |
| `union-members` | `add_union_members`, `edit_union-members` | `first_name`, `last_name`, `email`, `union` |

The JS uses `modal.dataset.table` to map UI interaction to the correct backend route automatically.