## Authentication Layer — Detailed Notes

### Overview
This app uses **two OAuth providers** (Microsoft and Google) for login, manages user roles using a custom `User` class, and protects routes via `Flask-Login`.
The authentication stack includes:
- `Flask-Login`: session & user identity management
- `msal`: Microsoft login
- `authlib`: Google login
- Role enforcement using MariaDB (internal vs. external users)
## 1. **Flask-Login Initialization**
```python
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'home'  # Redirect if not logged in
```
### Notes:
- `LoginManager` is initialized at the app level.
- The default redirect view for unauthorized users is set to `'home'`.
## 2. **User Class for Session Handling**
```python
class User(UserMixin):
    def __init__(self, email):
        self.id = email
        self.role = self.get_role()

    def get_role(self):
        internal = InternalUsers.query.filter_by(email=self.id).first()
        if internal:
            return 'internal'
        external = ExternalUsers.query.filter_by(email=self.id).first()
        if external:
            return external.union  # e.g., 'IUEC' or 'BLET'
        return None

    def get_id(self):
        return self.id
```
### Notes:
- Inherits from `UserMixin` to work with Flask-Login.
- Gets user role from database.
- Uses `email` as unique identifier
## 3. **User Loader Callback**
```python
@login_manager.user_loader
def load_user(email):
    if InternalUsers.query.filter_by(email=email).first() or ExternalUsers.query.filter_by(email=email).first():
        print("load_user called with:", email)
        return User(email)
    return None
```
### Notes:
- Called automatically by Flask-Login when a session exists.
- Ensures that user still exists in whitelist before loading session.
## 4. **Microsoft OAuth Flow (`msal`)**
### Configuration/Helper Function:
```python
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["User.Read"]

def _build_msal_app(cache=None):
    return msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
        token_cache=cache
    )
```
### Authorization Route:
Builds redirection to Microsoft login
- Create current state (a random string) for validating the current tab/window is the one that's asking for a request
```python
@app.route("/auth/microsoft")
def microsoft_login():
    session['state'] = str(uuid.uuid4())
    auth_url = _build_msal_app().get_authorization_request_url(
        scopes=SCOPE,
        state=session['state'],
        redirect_uri=redirect_uri,
        prompt="login"
    )
    return redirect(auth_url)
```
### Redirect Handler:
Handles the info after user logs in to handle redirection
- Define the correct route. `REDIRECT_PATH` is the redirect uri
- Ensure the states match so other sites/tabs can't access the current browser window
- Handle errors if user Microsoft account was not logged in and display error to user
- Check if code is given by Microsoft, meaning when the user comes back, a code comes back with them.
- Prepare a token cache to store the result with `SerializableTokenCache()`. Exchange code for access token to compare for later.
- Extract and validate user identity by using the `id_token_claims` (which stores user info) to get the current users email. Then you can check if such user exists in a database/whitelist
```python
@app.route(REDIRECT_PATH)
def microsoft_authorized():
    if request.args.get('state') != session.get("state"):
        flash("Get wrecked n00b", "error")
        return redirect(url_for("home"))

    if "code" in request.args:
        result = _build_msal_app().acquire_token_by_authorization_code(
            request.args['code'],
            scopes=SCOPE,
            redirect_uri=redirect_uri
        )
        email = result.get("id_token_claims", {}).get("preferred_username")
        if email:
            user = User(email)
            login_user(user)
            return redirect(url_for('inthome' if user.role == 'internal' else 'exthome'))
    
    flash("Access denied", "error")
    return redirect(url_for("home"))
```
## 5. **Google OAuth Flow (`authlib`)**
### Configuration:
```python
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_ID"),
    client_secret=os.getenv("GOOGLE_SECRET"),
    server_metadata_url=os.getenv("GOOGLE_DISCOVERY_URL"),
    client_kwargs={'scope': 'openid email profile'}
)
```
### Authorization:
Build redirection for Google
- Same as Microsoft minus the `scope` and the `promt`
```python
@app.route('/auth/google')
def google_login():
    session['state'] = str(uuid.uuid4())
    redirect_uri = url_for('google_authorized', _external=True)
    return google.authorize_redirect(redirect_uri, state=session['state'], prompt='select_account')
```
### Redirect Handler:
```python
@app.route('/authorize/google')
def google_authorized():
    if request.args.get('state') != session.get("state"):
        flash("Get wrecked n00b", "error")
        return redirect(url_for("home"))
    
    token = google.authorize_access_token()
    user_info = google.parse_id_token(token, None)
    email = user_info.get("email")

    if email:
        user = User(email)
        login_user(user)
        return redirect(url_for('inthome' if user.role == 'internal' else 'exthome'))

    flash("Access denied", "error")
    return redirect(url_for("home"))
```
## 6. **Session Termination**
```python
@app.route('/logout')
@login_required
def logout():
    logout_user()       # Flask-Login clears the session
    session.clear()     # Manual cleanup of Flask session
    return redirect(url_for('home'))
```
### Notes:
- All protected views use `@login_required`
- `current_user.role` is used to dynamically route or restrict functionality