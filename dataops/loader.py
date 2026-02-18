from dbmanager import db
from .models import Cleaned, UserLog

# For inserting cleaned structured data
def insert_cleaned_data(df):
    rows = df.to_dict(orient='records')
    db.session.bulk_insert_mappings(Cleaned, rows)
    db.session.commit()

# For inserting user l0gs
def insert_log(user, file, action):
    new_action = UserLog(user=user, file=file, action=action)
    db.session.add(new_action)
    db.session.commit()