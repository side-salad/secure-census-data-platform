from dbmanager import db
from .models import BlobOriginal, BlobCleaned
from datetime import datetime

# Encapsulates logic for inserting uncleaned blob
def unclean_blob(filename, union, email, blob_data, file_type):
    file = BlobOriginal(
        filename=filename,
        union=union,
        email=email,
        file_blob=blob_data,
        file_type=file_type,
        uploaded_at=datetime.now()
    )
    db.session.add(file)
    db.session.commit()

# Encapsulates logic for inserting cleaned blob
def clean_blob_excel(filename, union, email, excel_blob: bytes, rowcount):
    cleaned_filename = filename.rsplit('.', 1)[0] + ".xlsx"
    upload = BlobCleaned(
        filename=cleaned_filename,
        union=union,
        email=email,
        file_blob=excel_blob,
        file_type="xlsx",
        uploaded_at=datetime.now(),
        rowcount=rowcount,
        status="0"
    )
    db.session.add(upload)
    db.session.commit()