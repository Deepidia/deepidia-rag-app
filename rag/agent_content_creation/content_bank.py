import os
from rag import ViralTopicGenerator
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

def color_header(spreadsheet_id):
    creds = Credentials.from_service_account_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    service = build('sheets', 'v4', credentials=creds)
    requests = [
        {
            "repeatCell": {
                "range": {
                    "sheetId": 0,  # Assumes first sheet
                    "startRowIndex": 0,
                    "endRowIndex": 1
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {
                            "red": 0.13,   # Deep blue
                            "green": 0.45,
                            "blue": 0.71
                        },
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE",
                        "textFormat": {
                            "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},  # White text
                            "fontSize": 12,
                            "bold": True
                        },
                        "wrapStrategy": "WRAP"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"
            }
        },
        {
            "updateBorders": {
                "range": {
                    "sheetId": 0,
                    "startRowIndex": 0,
                    "endRowIndex": 1
                },
                "top":    {"style": "SOLID", "width": 2, "color": {"red": 0, "green": 0, "blue": 0}},
                "bottom": {"style": "SOLID", "width": 2, "color": {"red": 0, "green": 0, "blue": 0}},
                "left":   {"style": "SOLID", "width": 2, "color": {"red": 0, "green": 0, "blue": 0}},
                "right":  {"style": "SOLID", "width": 2, "color": {"red": 0, "green": 0, "blue": 0}},
                "innerHorizontal": {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}},
                "innerVertical":   {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}}
            }
        },
        {
            # Enable text wrapping for all columns (rows 1 to 1000)
            "repeatCell": {
                "range": {
                    "sheetId": 0,
                    "startRowIndex": 0,
                    "endRowIndex": 1000  # Adjust as needed
                },
                "cell": {
                    "userEnteredFormat": {
                        "wrapStrategy": "WRAP"
                    }
                },
                "fields": "userEnteredFormat.wrapStrategy"
            }
        },
        {
            # Set column width for Title (E, index 4) and Description (F, index 5)
            "updateDimensionProperties": {
                "range": {
                    "sheetId": 0,
                    "dimension": "COLUMNS",
                    "startIndex": 4,  # Title column (E)
                    "endIndex": 5
                },
                "properties": {
                    "pixelSize": 300  # Adjust width as needed
                },
                "fields": "pixelSize"
            }
        },
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": 0,
                    "dimension": "COLUMNS",
                    "startIndex": 5,  # Description column (F)
                    "endIndex": 6
                },
                "properties": {
                    "pixelSize": 500  # Adjust width as needed
                },
                "fields": "pixelSize"
            }
        },
        {
            # Center align horizontally and vertically for columns 0-4 (model_type, category, scope, keyword, title)
            "repeatCell": {
                "range": {
                    "sheetId": 0,
                    "startColumnIndex": 0,
                    "endColumnIndex": 5,
                    "startRowIndex": 1,  # Data rows only
                    "endRowIndex": 1000
                },
                "cell": {
                    "userEnteredFormat": {
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE"
                    }
                },
                "fields": "userEnteredFormat.horizontalAlignment,userEnteredFormat.verticalAlignment"
            }
        }
    ]
    body = {"requests": requests}
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()

def generate_ideas_and_store(
    model_type, category, scope, keyword, num_ideas, username
):
    # Generate ideas
    generator = ViralTopicGenerator(model_type=model_type)
    ideas = generator.generate_viral_ideas(
        topic_type=category, scope=scope, keyword=keyword, num_ideas=num_ideas
    )

    # Create a local folder for the user if it doesn't exist
    user_folder = os.path.join(os.getcwd(), username)
    os.makedirs(user_folder, exist_ok=True)

    # Connect to Google Sheets
    gs_scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", gs_scope)
    client = gspread.authorize(creds)

    # Create a new spreadsheet with the username if it doesn't exist
    try:
        spreadsheet = client.open(username)
        sheet = spreadsheet.sheet1
    except gspread.SpreadsheetNotFound:
        spreadsheet = client.create(username)
        # Make the spreadsheet public as viewer
        spreadsheet.share(None, perm_type='anyone', role='reader')
        sheet = spreadsheet.sheet1

    # Define the expected header
    header = ["model_type", "category", "scope", "keyword", "title", "description"]
    all_values = sheet.get_all_values()
    if not all_values or all_values[0] != header:
        # Insert header at the top if missing or incorrect
        sheet.insert_row(header, 1)
        # Color the header row
        color_header(spreadsheet.id)

    # Write ideas to sheet
    for idea in ideas:
        title = idea.get("title", "")
        description = idea.get("description", "")
        sheet.append_row([
            model_type,
            category,
            scope,
            keyword,
            title,
            description
        ])

    # Get spreadsheet URL
    spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}"
    drive_url = f"https://drive.google.com/drive/folders/{spreadsheet.id}"  # This is not always a folder, but for reference

    return ideas, spreadsheet_url, drive_url

if __name__ == "__main__":
    # Example usage for testing
    model_type = "gemini"
    category = "Technology"
    scope = "Trending Now"
    keyword = "AI"
    num_ideas = 5
    username = "test8"  # Replace with the actual username

    ideas, spreadsheet_url, drive_url = generate_ideas_and_store(
        model_type, category, scope, keyword, num_ideas, username
    )
    print("Ideas generated and stored:")
    for idea in ideas:
        print(f"- {idea.get('title', '')}: {idea.get('description', '')}")
    print(f"Spreadsheet URL: {spreadsheet_url}")
    print(f"Google Drive URL: {drive_url}")