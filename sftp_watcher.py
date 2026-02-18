from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
from censuscleaning import load_file, column_map_final, clean_items, remove_dupes
from dataops.blob import unclean_blob, clean_blob_excel
import io, os

WATCH_PATH = os.getenv("SFTP_WATCH")

def start_observer():
    event_handler = UploadHandler()
    observer = PollingObserver()
    observer.schedule(event_handler, WATCH_PATH, recursive=True)
    observer.start()
    print(f"WATCHING: {WATCH_PATH}")
    observer.join()
    observer.is_alive()

def process_file(path, email="sftp"):
    from app import app 
    with app.app_context():
        filename = os.path.basename(path)
        file_type = filename.split('.')[-1].lower()
        label = os.path.basename(os.path.dirname(path))

        df = load_file(file_type, path)
        with open(path, "rb") as f:
            file_bytes = f.read()

        unclean_blob(filename, label, email, file_bytes, file_type)

        column_mapped_df = column_map_final(df.columns, df)
        cleaned_df = remove_dupes(clean_items(column_mapped_df))

        output = io.BytesIO()
        cleaned_df.to_excel(output, index=False, engine='xlsxwriter')
        cleaned_bytes = output.getvalue()
        clean_blob_excel(filename, label, email, cleaned_bytes, len(df))

        print(f"Da file: {filename}")


class UploadHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            filename = os.path.basename(event.src_path)
            if filename.startswith(".") or not filename.lower().endswith(('.csv', '.xlsx', '.xls', '.txt')):
                return
            try:
                print(f"Uploaded: {event.src_path}")
                process_file(event.src_path)
            except Exception as e:
                print(f"Bad upload: {event.src_path}: {e}")