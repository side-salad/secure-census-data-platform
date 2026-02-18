# This file is to define tables

from dbmanager import db
from datetime import datetime

# Clean DB model
class Cleaned(db.Model):
    __tablename__ = 'cleaned_structured'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255), nullable=True)
    last_name = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    address_one = db.Column(db.String(255), nullable=True)
    address_two = db.Column(db.String(255), nullable=True)
    zip_code = db.Column(db.String(255), nullable=True)
    state = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(100), nullable=True)
    organization = db.Column(db.String(100), nullable=True)
    local = db.Column(db.String(255), nullable=True)
    dob = db.Column(db.String(255), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.now())

# BLOB storage for cleaned DB
class BlobCleaned(db.Model):
    __tablename__ = 'blob_cleaned'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    union = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    file_blob = db.Column(db.LargeBinary(length=4294967295), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.now())
    rowcount = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(255), nullable=False, default="0")

# BLOB storage DB model for original data
class BlobOriginal(db.Model):
    __tablename__ = 'blob_original'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    union = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    file_blob = db.Column(db.LargeBinary(length=4294967295), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.now())

# Storage for internal users whitelist
class InternalUsers(db.Model):
    __tablename__ = 'internal_whitelist'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.now())

# Storage for internal users whitelist
class ExternalUsers(db.Model):
    __tablename__ = 'external_whitelist'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    union = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.now())

# Storage for logging actions by internal users
class UserLog(db.Model):
    __tablename__ = 'user_log'

    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(255), nullable=False)
    file = db.Column(db.String(255), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now())