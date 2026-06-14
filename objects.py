import csv
import calendar
import datetime
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests

app = FastAPI()
CSV_FILENAME = "cycle_log.csv"

class LocalCalendar:
    def __init__(self, year: int):
        self.year = year
        self.setup_local_csv()

    def setup_local_csv(self):
        """Creates the CSV structure with headers and blank entries if it doesn't exist."""
        headers = ["Year", "Month", "Day", "Period?", "Feelings/Symptoms", "Machine Learning Prediction"]
        
        # If the file already exists, we do not want to overwrite user data
        if os.path.exists(CSV_FILENAME):
            print(f"Using existing local storage: {CSV_FILENAME}")
            return

        rows_to_insert = []
        years_to_generate = [2025, 2026, 2027]

        for yr in years_to_generate:
            for mo_idx in range(1, 13):
                mo_name = calendar.month_name[mo_idx]
                _, max_days = calendar.monthrange(yr, mo_idx)

                for dy in range(1, max_days + 1):
                    # Default template rows matching your exact grid configuration
                    rows_to_insert.append([yr, mo_name, dy, "False", "", ""])

        # Write to local disk file
        with open(CSV_FILENAME, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(rows_to_insert)
        print(f"Created new local database grid: {CSV_FILENAME}")

    def send_push_notifications(self, message):
        url = "https://pushover.net"
        data = {
            "token": "asc6ez4h3gsxx62gjrcsu4jj13fnrw",
            "user": "uadz4xtj1hni91uvwurr4je53gskhi",
            "message": message,
            "sound": "flick"
        }
        try:
            requests.post(url, data=data, timeout=5)
        except Exception as e:
            print(f"Notification Network Error: {e}")

    def update_local_record(self, year: int, month_name: str, day: int, column_name: str, value: str):
        """Reads the CSV into memory, updates the target row, and writes it back."""
        formatted_month = month_name.title()
        updated_rows = []
        headers = []
        record_found = False

        if not os.path.exists(CSV_FILENAME):
            raise FileNotFoundError("Database file missing.")

        with open(CSV_FILENAME, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            headers = next(reader)
            col_idx = headers.index(column_name)

            for row in reader:
                # Check for matching structural row index
                if int(row[0]) == year and row[1] == formatted_month and int(row[2]) == day:
                    row[col_idx] = value
                    record_found = True
                updated_rows.append(row)

        if record_found:
            # Overwrite the file with the updated array rows
            with open(CSV_FILENAME, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(headers)
                writer.writerows(updated_rows)
        else:
            print(f"Warning: No match found for {year}-{formatted_month}-{day}")


# Instantiate database structure on runtime boot
tracker_instance = LocalCalendar(2026)

class LogEntry(BaseModel):
    year: int
    month: str
    day: int
    period: bool
    feelings: str

@app.get("/", response_class=HTMLResponse)
def serve_ui():
    with open("index.html", "r") as file:
        return file.read()

@app.post("/api/log")
def log_cycle_data(entry: LogEntry):
    try:
        # 1. Update the Period Column
        tracker_instance.update_local_record(
            entry.year, entry.month, entry.day, "Period?", str(entry.period)
        )
        
        # 2. Update the Symptoms Column
        tracker_instance.update_local_record(
            entry.year, entry.month, entry.day, "Feelings/Symptoms", entry.feelings
        )

        # Trigger notification if period toggle is true
        if entry.period:
            tracker_instance.send_push_notifications(f"Period has begun on {entry.month} {entry.day}!")

        return {"status": "success", "message": "Saved to local CSV file successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
