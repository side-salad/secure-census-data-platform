# Flask App Structure
![[Screenshot 2025-07-15 094108.png]]

### 1. **App Entry Point (`app.py`)**
The central file that initializes and runs the Flask server.
#### Key Responsibilities:
- App creation and config loading (`Flask(__name__)`, `.env`)
- Setting up OAuth providers (Microsoft via MSAL, Google via Authlib)
- Connecting to database via `connect_db(app)`
- Registering Flask-Login manager and user loader
- Defining all route endpoints
- Running the app (`app.run()`)
- 8 hour session limits 
### 2. **Authentication Layer**
Handles user login/logout and identity resolution.
#### Key Files & Modules:
- **`authlib`, `msal`**: OAuth for Google and Microsoft
- **`User` class** (in `app.py`):
    - Subclass of `UserMixin`
    - Dynamically determines role (`internal`, or union name)
- **Flask-Login**:
    - Session management
    - `@login_required` decorator to protect routes
    - `load_user()` function links session `email` to a `User` object
#### Notes:
- Users are whitelisted via two DB tables: `InternalUsers`, `ExternalUsers`
- Post-login redirects are role-based (`/internal/files` or `/external`)
### 3. **Routes Layer**
Defines the web endpoints, grouped by function.
#### Key Routes:
**All Users**
- **`/`**: Public homepage
- **`/auth/*` and `/authorize/*`**: OAuth flows
- **`/logout`**: Ends session and clears Flask session
**External Users**
- **`/external`**: Upload dashboard for union users
- **`/upload`**: External users' file upload interface
**Internal Users**
- **`/download/<int:file_id>`**: Internal users download cleaned files
- **`/preview/<int:file_id>`**: Internal users preview cleaned census data (first 10 rows)
- **`/internal/files`**: Admin dashboard with all union census files listing
- **`/add_admin`** and **`/add_union_member`**: Internal users ability to add new entries (admin members or union members)
- **`/edit_admin-members`** and **`/edit_union-members`**: Internal users ability to edit users
- **`/delete_admin-members`** and **`/delete_union-members`**: Internal users ability to delete users
- **`/admin`**: Admin dashboard for portal users
#### Notes:
- Most routes check `current_user.role` before rendering or redirecting
- Most routes validate session users via `@login_required` decorator
- `/upload` is POST/GET and handles all data validation and pipeline triggering
### 4. **Data Operations Layer (`dataops/`)**
Handles core logic for data transformation and file storage.
#### Key Files:
- **`blob.py`**
    - `unclean_blob()` – Saves uploaded file to DB
    - `clean_blob_excel()` – Saves cleaned version to DB
- **`models.py`**
    - SQLAlchemy models for BLOBs and user tables
#### Notes:
- Files are loaded and cleaned via the census_cleaning python module
- File conversions are handled using `pandas` and `xlsxwriter`
- Cleaned files are kept in-memory using `io.BytesIO()`
### 5. **Templates Layer (`templates/`)**
HTML files rendered via `render_template`.
#### Files:
- `home.html` – Public landing page
- `upload.html` – Drag-and-drop file interface
- `inthome.html` – Admin dashboard for file listings
- `exthome.html` – External user’s landing post-login
- `admin.html` – Internal user's dashboard for viewing portal members
#### Notes:
- Static assets assumed but not shown (e.g., CSS/JS for drag-and-drop)
### 5. **Security and Config**
- `SECRET_KEY`, OAuth credentials, and redirect paths are loaded from `.env`
- All admin actions are logged in a separate table in database