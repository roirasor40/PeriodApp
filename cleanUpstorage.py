import gspread

gc = gspread.service_account(filename='credentials.json')

print("Fetching all spreadsheets accessed by this service account...")
all_sheets = gc.openall()

if not all_sheets:
    print("No spreadsheets found!")
else:
    for sheet in all_sheets:
        try:
            print(f"Attempting to delete: {sheet.title} (ID: {sheet.id})")
            gc.del_spreadsheet(sheet.id)
            print(f"Successfully deleted: {sheet.title}")
        except gspread.exceptions.APIError as e:
            # Catch the 403 error and explain what's happening
            if "403" in str(e):
                print(f"Skipping '{sheet.title}': Service account does not have permission to delete this file.")
            else:
                print(f"Could not delete '{sheet.title}' due to an unexpected error: {e}")

print("\nCleanup process complete!")