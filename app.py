'''
Description: A union interface with the secure (oAuth) census portal in one of two transmission methods 
(SFTP, web) and the pipeline begins: the census file is moved to our onsite resources, processed, 
permanently stored, and becomes available on the internal (secure, oAuth) census portal. Admin controls
available to remove, edit, or add census portal members as well as other admin members.

Author: Bikrum Kahlon
'''

import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, send_file, session, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pandas as pd
from dbmanager import db
from dbmanager.schema import connect_db
from dataops.models import BlobCleaned, InternalUsers, ExternalUsers
from dataops.blob import unclean_blob, clean_blob_excel
from dataops.loader import insert_log
from censuscleaning import load_file, column_map_final, clean_items, remove_dupes
from dragdrop import init_dragdrop
from authlib.integrations.flask_client import OAuth
import msal
import uuid
import io
import threading
from sftp_watcher import start_observer
from datetime import datetime, timedelta
from sqlalchemy import func, text



"""
V  Helper functions and app setups  V
"""

# Initialized app and added session  limits
app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv('SECRET_KEY')
app.permanent_session_lifetime = timedelta(hours=8)

# Initialize drag and drop modulle in app
init_dragdrop(app)

# Microsoft oAuth config
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
REDIRECT_PATH = os.getenv("REDIRECT_PATH")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = [os.getenv("SCOPE", "User.Read")]

# Aquire tokens for microsoft
def _build_msal_app(cache=None):
    return msal.ConfidentialClientApplication(CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET, token_cache=cache)
redirect_uri = os.getenv('REDIRECT_URI')

# Google oAuth config
oauth = OAuth(app)
google = oauth.register(name='google', client_id=os.getenv("GOOGLE_ID"), client_secret=os.getenv("GOOGLE_SECRET"), server_metadata_url=os.getenv("GOOGLE_DISCOVERY_URL"), client_kwargs={'scope': 'openid email profile'})

# Loading information to connect to MariaDB
connect_db(app)

# Created table in database for whitelists
int_whitelist={'first_name':['Big', 'Joe', 'Test'], 'last_name':['Pizza', 'Smo', 'Test'], 'emails': ["brandon@email.com", "uniononetest@email.com", "idk@yea.com"]}
ext_whitelist={'first_name':['Bikrum', 'First', 'What'], 'last_name':['Kahlon', 'Last', 'The'], 'emails': ["bikrum@email.com", "iuec@email.com", 'blet@email.com'], 'union': ['Test Union', 'Test Union', 'Test Union']}
with app.app_context():
    for first_name, last_name, email in zip(int_whitelist['first_name'], int_whitelist['last_name'], int_whitelist['emails']):
        if not InternalUsers.query.filter_by(email=email).first():
            db.session.add(InternalUsers(first_name=first_name, last_name=last_name, email=email))
    for first_name, last_name, email, union in zip(ext_whitelist['first_name'], ext_whitelist['last_name'], ext_whitelist['emails'], ext_whitelist['union']):
        if not ExternalUsers.query.filter_by(email=email).first():
            db.session.add(ExternalUsers(first_name=first_name, last_name=last_name, email=email, union=union))
    db.session.commit()

# Flask login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'home'

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
            return external.union
        return None
    def get_id(self):
        return self.id
        
# Assigns function to decorator, called automatically when @login_required is used
@login_manager.user_loader
def load_user(email):
    if InternalUsers.query.filter_by(email=email).first() or ExternalUsers.query.filter_by(email=email).first():
        print("load_user called with:", email)
        return User(email)
    return None



"""
V  Da app routes  V
"""


# Homepage
@app.route("/")
def home():
    return render_template('home.html')

# Microsoft oAuth
@app.route("/auth/microsoft")
def microsoft_login():
    session['state'] = str(uuid.uuid4()) 
    auth_url = _build_msal_app().get_authorization_request_url(scopes=SCOPE, state=session['state'], redirect_uri=redirect_uri, prompt="login")
    return redirect(auth_url)

# Google oAuth
@app.route('/auth/google')
def google_login():
    session['state'] = str(uuid.uuid4())
    redirect_uri = url_for('google_authorized', _external=True)
    return google.authorize_redirect(redirect_uri, state=session['state'], prompt='select_account')

# Handle redirects after login from microsoft
@app.route(REDIRECT_PATH)
def microsoft_authorized():
    if request.args.get('state') != session.get("state"):
        flash("Login error, try again", "error")
        return redirect(url_for("home"))

    if "error" in request.args:
        flash(f"Login failed: {request.args.get('error_description', 'Unknown error')}", "error")
        return redirect(url_for("home"))

    if "code" in request.args:
        cache = msal.SerializableTokenCache()
        result = _build_msal_app(cache).acquire_token_by_authorization_code(request.args['code'], scopes=SCOPE, redirect_uri=redirect_uri)
        if "id_token_claims" in result:
            email = result["id_token_claims"].get("preferred_username")
            if email:
                if InternalUsers.query.filter_by(email=email).first() or ExternalUsers.query.filter_by(email=email).first():
                    user = User(email)
                    login_user(user)
                    session.permanent = True
                    if user.role == 'internal':
                        return redirect(url_for('inthome'))
                    else:
                        return redirect(url_for('exthome'))
        flash("Access denied: unauthorized email", "error")
        return redirect(url_for("home"))
    flash("Access denied: unauthorized email", "error")
    return redirect(url_for("home"))

# Redirects after google login
@app.route('/authorize/google')
def google_authorized():
    if request.args.get('state') != session.get("state"):
        flash("Login error, try again", "error")
        return redirect(url_for("home"))
    
    token = google.authorize_access_token()
    user_info = google.parse_id_token(token, None)
    email = user_info.get("email")

    if email:
        if InternalUsers.query.filter_by(email=email).first() or ExternalUsers.query.filter_by(email=email).first():
            user = User(email)
            login_user(user)
            session.permanent = True
            if user.role == 'internal':
                return redirect(url_for('inthome'))
            else:
                return redirect(url_for('exthome'))
    flash("Access denied: unauthorized email", "error")
    return redirect(url_for("home"))

# Census upload actions
@app.route("/upload", methods=['GET', 'POST'])
@login_required
def upload_file():
    if not ExternalUsers.query.filter_by(email=current_user.id).first():
        return redirect(url_for('home'))
    # Gets current user
    label = current_user.role

    if request.method == 'POST':
        file = request.files['file']
        if not file or file.filename == '':
            return "No file Uploaded"
        
        # Validate and load file
        file_type = file.filename.split('.')[-1].lower()
        df = load_file(file, file.filename)
        
        # Turns the original uploaded file into bytes and uploads as BLOB
        file.stream.seek(0)
        file_bytes = file.read()
        unclean_blob(file.filename, label, current_user.id, file_bytes, file_type)
        
        # Column Mapping/Cleaning
        column_mapped_df = column_map_final(df)
        column_map_df_cleaned = remove_dupes(clean_items(column_mapped_df))
        
        # Converts cleaned file to excel and then into bytes for BLOB storage
        output = io.BytesIO()
        column_map_df_cleaned.to_excel(output, index=False, engine='xlsxwriter')
        test_bytes = output.getvalue()
        clean_blob_excel(file.filename, label, current_user.id, test_bytes, len(df))
        return redirect(request.url)
    return render_template("upload.html")

# File download route for internal users
@app.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    if current_user.role != "internal":
        return redirect(url_for('home'))
    # Get BLOB by id for download
    file = BlobCleaned.query.get(file_id)
    if file:
        insert_log(current_user.id, file.filename, 'download')
        return send_file(io.BytesIO(file.file_blob), as_attachment=True, download_name=file.filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    return "File not found"

# For previewing files in internal users
@app.route('/preview/<int:file_id>')
@login_required
def preview_file(file_id):
    if current_user.role != "internal":
        return redirect(url_for('home'))
    file = BlobCleaned.query.get(file_id)
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

# For updating the status of the census process
@app.route('/update-stage/<int:file_id>', methods=['POST'])
@login_required
def update_file_stage(file_id):
    if current_user.role != "internal":
        return redirect(url_for('home'))
    data = request.get_json()
    new_status = data.get('stage')
    file_record = BlobCleaned.query.get_or_404(file_id)
    file_record.status = new_status
    db.session.commit()
    return jsonify({'success': True, 'status': file_record.status})

# Internal users page (list of cleaned census's from MariaDb)
@app.route("/internal/files")
@login_required
def inthome():
    if current_user.role != 'internal':
        return redirect(url_for('home'))
    # Get metadata as dict for listing purposes
    files = BlobCleaned.query.with_entities(BlobCleaned.id, BlobCleaned.filename, BlobCleaned.union, BlobCleaned.email, BlobCleaned.uploaded_at, BlobCleaned.rowcount, BlobCleaned.status).order_by(BlobCleaned.uploaded_at.desc()).all()
    files_dict = [{'id': f.id, 'filename': f.filename, 'union': f.union, 'email': f.email, 'upload_date' : f.uploaded_at, 'rowcount': f.rowcount, 'status': f.status} for f in files]
    return render_template("inthome.html", files=files_dict)

# For adding admins
@app.route("/add_admin", methods=["POST"])
@login_required
def add_admin():
    if current_user.role != 'internal':
        return redirect(url_for('home.html'))
    data = request.get_json()
    if InternalUsers.query.filter_by(email=data['email']).first():
        return jsonify(success=False, message="Email already exists"), 400
    if '@unionone.com' not in data['email']:
        return jsonify(success=False, message="Email must end in @unionone.com"), 400
    new = InternalUsers(first_name=data['first_name'], last_name=data['last_name'], email=data['email'], uploaded_at=datetime.now())
    db.session.add(new)
    db.session.commit()
    return jsonify({**data, "upload_date": new.uploaded_at.strftime('%Y-%m-%d %H:%M')})

# For editing admins
@app.route("/edit_admin-members", methods=["POST"])
@login_required
def edit_admin():
    if current_user.role != 'internal':
        return redirect(url_for('home.html'))
    data = request.get_json()
    original_email = data.get("original_email")
    updated_email = data.get("email")
    if not original_email:
        return jsonify(success=False, message="Missing original email")
    email_clean = original_email.strip().lower()
    user = InternalUsers.query.filter(func.lower(func.trim(InternalUsers.email)) == email_clean).first()
    if original_email.strip().lower() != updated_email.strip().lower():
        bad = InternalUsers.query.filter(func.lower(func.trim(InternalUsers.email)) == updated_email.strip().lower()).first()
        if bad:
            return jsonify(success=False, message="Email already exists"), 400
    if user:
        user.first_name = data.get("first_name", user.first_name)
        user.last_name = data.get("last_name", user.last_name)
        user.email = updated_email 
        db.session.commit()
        return jsonify(success=True)
    else:
        return jsonify(success=False, message="User not found")

# For deleting admins
@app.route("/delete_admin-members", methods=["POST"])
@login_required
def delete_admin():
    if current_user.role != 'internal':
        return redirect(url_for('home.html'))
    data = request.get_json()
    original_email = data.get("original_email", data.get("email"))
    if not original_email:
        return jsonify(success=False, message="Missing email")
    email_clean = original_email.strip().lower()
    user = InternalUsers.query.filter(func.lower(func.trim(InternalUsers.email)) == email_clean).first()
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify(success=True)
    else:
        return jsonify(success=False, message="User not found")

# For adding union member
@app.route("/add_union_members", methods=["POST"])
@login_required
def add_union():
    if current_user.role != 'internal':
        return redirect(url_for('home.html'))
    data = request.get_json()
    if ExternalUsers.query.filter_by(email=data['email']).first():
        return jsonify(success=False, message="Email already exists"), 400
    new = ExternalUsers(first_name=data['first_name'], last_name=data['last_name'], email=data['email'], union=data['union'], uploaded_at=datetime.now())
    db.session.add(new)
    db.session.commit()
    return jsonify({**data, "upload_date": new.uploaded_at.strftime('%Y-%m-%d %H:%M')})

# For editing union members
@app.route("/edit_union-members", methods=["POST"])
@login_required
def edit_union():
    if current_user.role != 'internal':
        return redirect(url_for('home.html'))
    data = request.get_json()
    original_email = data.get("original_email")
    updated_email = data.get("email")
    if not original_email:
        return jsonify(success=False, message="Missing original email")
    email_clean = original_email.strip().lower()
    user = ExternalUsers.query.filter(func.lower(func.trim(ExternalUsers.email)) == email_clean).first()
    if original_email.strip().lower() != updated_email.strip().lower():
        bad = ExternalUsers.query.filter(func.lower(func.trim(ExternalUsers.email)) == updated_email.strip().lower()).first()
        if bad:
            return jsonify(success=False, message="Email already exists"), 400
    if user:
        user.first_name = data.get("first_name", user.first_name)
        user.last_name = data.get("last_name", user.last_name)
        user.email = updated_email 
        user.union = data.get("union", user.union)
        db.session.commit()
        return jsonify(success=True)
    else:
        return jsonify(success=False, message="User not found")

# For deleting union members
@app.route("/delete_union-members", methods=["POST"])
@login_required
def delete_union():
    if current_user.role != 'internal':
        return redirect(url_for('home.html'))
    data = request.get_json()
    original_email = data.get("original_email", data.get("email"))
    if not original_email:
        return jsonify(success=False, message="Missing email")
    email_clean = original_email.strip().lower()
    user = ExternalUsers.query.filter(func.lower(func.trim(ExternalUsers.email)) == email_clean).first()
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify(success=True)
    else:
        return jsonify(success=False, message="User not found")

# Admin page (for making changes >:3)
@app.route("/admin")
@login_required
def admin():
    if current_user.role != 'internal':
        return redirect(url_for('home.html'))
    
    admins_files = InternalUsers.query.with_entities(InternalUsers.first_name, InternalUsers.last_name, InternalUsers.email, InternalUsers.uploaded_at).order_by(InternalUsers.uploaded_at.desc()).all()
    admins = [{'first_name': f.first_name, 'last_name': f.last_name, 'email': f.email, 'upload_date': f.uploaded_at} for f in admins_files]
    
    last_uploads_raw = (db.session.query(BlobCleaned.email,func.max(BlobCleaned.uploaded_at).label("last_upload")).group_by(BlobCleaned.email).all())
    last_uploads = {email: str(upload_date)[:10] if upload_date else None for email, upload_date in last_uploads_raw}
    union_members_files = ExternalUsers.query.with_entities(ExternalUsers.first_name, ExternalUsers.last_name, ExternalUsers.email, ExternalUsers.union, ExternalUsers.uploaded_at).order_by(ExternalUsers.uploaded_at.desc()).all()
    union_members = [{'union': f.union, 'first_name': f.first_name, 'last_name': f.last_name, 'email': f.email, 'upload_date': f.uploaded_at, 'recent_upload': last_uploads.get(f.email) or " "} for f in union_members_files]

    sftp_files = BlobCleaned.query.filter(BlobCleaned.email == 'sftp').order_by(BlobCleaned.uploaded_at.desc()).all()
    sftp_users = [{'id': f.id, 'filename': f.filename, 'union': f.union, 'email': f.email, 'upload_date' : f.uploaded_at, 'rowcount': f.rowcount} for f in sftp_files]
    return(render_template('admin.html', union_members=union_members, admins=admins, sftp_users=sftp_users))

# External users page (drag and drop census upload)
@app.route("/external")
@login_required
def exthome():
    if current_user.role == 'internal':
        return redirect(url_for('home'))
    uploads = BlobCleaned.query \
        .filter_by(email=current_user.id) \
        .order_by(BlobCleaned.uploaded_at.desc()) \
        .with_entities(BlobCleaned.filename, BlobCleaned.uploaded_at) \
        .all()
    current_union = ExternalUsers.query.filter(ExternalUsers.email == current_user.id).first()
    uploads_list = [{'filename': u.filename, 'uploaded_at': u.uploaded_at.strftime('%Y-%m-%d %H:%M')} for u in uploads]
    return render_template("exthome.html", uploads=uploads_list, current_union=current_union)

# Logout process for current user
@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('home'))


if __name__ == "__main__":
    watcher_thread = threading.Thread(target=start_observer, daemon=True)
    watcher_thread.start()
    app.run(debug=False, host='0.0.0.0', use_reloader=False)