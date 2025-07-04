import os
import psycopg2
import csv
import json
import pandas as pd
from datetime import datetime
from rag import ViralTopicGenerator

# Database configuration
DATABASE_URL = "postgresql://myuser:mypassword@8.219.101.54:15432/mydatabase"

def get_db_connection():
    """
    Get PostgreSQL database connection
    """
    return psycopg2.connect(DATABASE_URL)

def user_exists(name):
    """
    Check if user exists in the database by name
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT name FROM users WHERE name = %s', (name,))
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return result is not None

def init_ideas_table():
    """
    Initialize ideas table in PostgreSQL
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    # Create ideas table with name as foreign key
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ideas (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL REFERENCES users(name) ON DELETE CASCADE,
            model_type TEXT NOT NULL,
            category TEXT NOT NULL,
            scope TEXT NOT NULL,
            keyword TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ideas_name ON ideas(name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ideas_created_at ON ideas(created_at)')
    conn.commit()
    cursor.close()
    conn.close()
    return "Ideas table initialized successfully"

def save_ideas_to_postgres(ideas, name, model_type, category, scope, keyword):
    """
    Save ideas to PostgreSQL database (using name directly)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    for idea in ideas:
        title = idea.get("title", "")
        description = idea.get("description", "")
        cursor.execute('''
            INSERT INTO ideas (name, model_type, category, scope, keyword, title, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (name, model_type, category, scope, keyword, title, description))
    conn.commit()
    cursor.close()
    conn.close()
    return f"Saved {len(ideas)} ideas to PostgreSQL for user '{name}'"

def export_ideas_to_csv(ideas, name, model_type, category, scope, keyword):
    """
    Export ideas to CSV file for spreadsheet import (appends to existing file)
    """
    # Create exports directory if it doesn't exist
    exports_dir = "exports"
    os.makedirs(exports_dir, exist_ok=True)
    
    # Use a fixed filename for the user (no timestamp)
    filename = f"{name}_ideas.csv"
    filepath = os.path.join(exports_dir, filename)
    
    # Define the header
    header = ["model_type", "category", "scope", "keyword", "title", "description", "created_at"]
    
    # Check if file exists to determine if we need to write header
    file_exists = os.path.exists(filepath)
    
    # Write ideas to CSV file (append mode)
    with open(filepath, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header only if file doesn't exist
        if not file_exists:
            writer.writerow(header)
        
        # Append new ideas
        for idea in ideas:
            title = idea.get("title", "")
            description = idea.get("description", "")
            created_at = datetime.now().isoformat()
            
            writer.writerow([
                model_type,
                category,
                scope,
                keyword,
                title,
                description,
                created_at
            ])
    
    return filepath

def export_ideas_to_json(ideas, name, model_type, category, scope, keyword):
    """
    Export ideas to JSON file (appends to existing file)
    """
    # Create exports directory if it doesn't exist
    exports_dir = "exports"
    os.makedirs(exports_dir, exist_ok=True)
    
    # Use a fixed filename for the user (no timestamp)
    filename = f"{name}_ideas.json"
    filepath = os.path.join(exports_dir, filename)
    
    # Check if file exists to load existing data
    existing_data = {"metadata": {}, "ideas": []}
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as jsonfile:
                existing_data = json.load(jsonfile)
        except:
            # If file is corrupted, start fresh
            existing_data = {"metadata": {}, "ideas": []}
    
    # Prepare data for JSON
    data = {
        "metadata": {
            "user_id": name,
            "last_updated": datetime.now().isoformat(),
            "total_ideas": len(existing_data.get("ideas", [])) + len(ideas),
            "last_batch": {
                "model_type": model_type,
                "category": category,
                "scope": scope,
                "keyword": keyword,
                "created_at": datetime.now().isoformat(),
                "batch_size": len(ideas)
            }
        },
        "ideas": existing_data.get("ideas", []) + ideas
    }
    
    # Write ideas to JSON file
    with open(filepath, 'w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, indent=2, ensure_ascii=False)
    
    return filepath

def export_ideas_to_excel(ideas, name, model_type, category, scope, keyword):
    """
    Export ideas to Excel file (appends to existing file)
    """
    # Create exports directory if it doesn't exist
    exports_dir = "exports"
    os.makedirs(exports_dir, exist_ok=True)
    
    # Use a fixed filename for the user (no timestamp)
    filename = f"{name}_ideas.xlsx"
    filepath = os.path.join(exports_dir, filename)
    
    # Prepare data for Excel
    data = []
    for idea in ideas:
        title = idea.get("title", "")
        description = idea.get("description", "")
        created_at = datetime.now().isoformat()
        
        data.append({
            "model_type": model_type,
            "category": category,
            "scope": scope,
            "keyword": keyword,
            "title": title,
            "description": description,
            "created_at": created_at
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Check if file exists to determine if we need to append or create new
    if os.path.exists(filepath):
        try:
            # Read existing Excel file
            existing_df = pd.read_excel(filepath)
            # Concatenate with new data
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            # Write back to Excel
            combined_df.to_excel(filepath, index=False)
        except:
            # If file is corrupted, create new
            df.to_excel(filepath, index=False)
    else:
        # Create new Excel file
        df.to_excel(filepath, index=False)
    
    return filepath

def get_user_ideas_from_postgres(name, limit=50):
    """
    Retrieve ideas from PostgreSQL for a specific user by name
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT model_type, category, scope, keyword, title, description, created_at
        FROM ideas
        WHERE name = %s
        ORDER BY created_at DESC
        LIMIT %s
    ''', (name, limit))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    ideas = []
    for row in results:
        ideas.append({
            "model_type": row[0],
            "category": row[1],
            "scope": row[2],
            "keyword": row[3],
            "title": row[4],
            "description": row[5],
            "created_at": row[6].isoformat() if row[6] else None
        })
    return ideas

def get_user_stats(name):
    """
    Get statistics for a user by name
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    # Total ideas count
    cursor.execute('SELECT COUNT(*) FROM ideas WHERE name = %s', (name,))
    total_ideas = cursor.fetchone()[0]
    # Ideas by category
    cursor.execute('SELECT category, COUNT(*) FROM ideas WHERE name = %s GROUP BY category', (name,))
    ideas_by_category = dict(cursor.fetchall())
    # Recent activity
    cursor.execute('SELECT created_at FROM ideas WHERE name = %s ORDER BY created_at DESC LIMIT 1', (name,))
    last_activity = cursor.fetchone()
    last_activity = last_activity[0].isoformat() if last_activity and last_activity[0] else None
    # Get user info
    cursor.execute('SELECT firstName, lastName, email, name FROM users WHERE name = %s', (name,))
    user_info = cursor.fetchone()
    cursor.close()
    conn.close()
    return {
        "name": name,
        "user_info": {
            "firstName": user_info[0] if user_info else None,
            "lastName": user_info[1] if user_info else None,
            "email": user_info[2] if user_info else None,
            "name": user_info[3] if user_info else None
        },
        "total_ideas": total_ideas,
        "ideas_by_category": ideas_by_category,
        "last_activity": last_activity
    }

def get_all_users_with_ideas():
    """
    Get all users who have generated ideas
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DISTINCT u.id, u.firstName, u.lastName, u.email, u.name,
               COUNT(i.id) as idea_count
        FROM users u
        LEFT JOIN ideas i ON u.id = i.user_id
        GROUP BY u.id, u.firstName, u.lastName, u.email, u.name
        HAVING COUNT(i.id) > 0
        ORDER BY idea_count DESC
    ''')
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    users = []
    for row in results:
        users.append({
            "user_id": row[0],
            "firstName": row[1],
            "lastName": row[2],
            "email": row[3],
            "name": row[4],
            "idea_count": row[5]
        })
    
    return users

def generate_ideas_and_store_postgres(
    model_type, category, scope, keyword, num_ideas, name,
    export_formats=["csv"]
):
    """
    Generate ideas and store them in PostgreSQL with optional export (using name directly)
    """
    if not user_exists(name):
        return None, f"User '{name}' does not exist in the database", {}
    generator = ViralTopicGenerator(model_type=model_type)
    ideas = generator.generate_viral_ideas(
        topic_type=category, scope=scope, keyword=keyword, num_ideas=num_ideas
    )
    storage_message = save_ideas_to_postgres(ideas, name, model_type, category, scope, keyword)
    export_info = {}
    if "csv" in export_formats or "both" in export_formats:
        csv_filepath = export_ideas_to_csv(ideas, name, model_type, category, scope, keyword)
        export_info["csv"] = {
            "filepath": csv_filepath,
            "download_url": f"/api/v1/download_csv/{name}",
            "message": "CSV file updated successfully"
        }
    if "json" in export_formats or "both" in export_formats:
        json_filepath = export_ideas_to_json(ideas, name, model_type, category, scope, keyword)
        export_info["json"] = {
            "filepath": json_filepath,
            "download_url": f"/api/v1/download_json/{name}",
            "message": "JSON file updated successfully"
        }
    if "excel" in export_formats or "both" in export_formats:
        excel_filepath = export_ideas_to_excel(ideas, name, model_type, category, scope, keyword)
        export_info["excel"] = {
            "filepath": excel_filepath,
            "download_url": f"/api/v1/download_excel/{name}",
            "message": "Excel file updated successfully"
        }
    return ideas, storage_message, export_info

def migrate_ideas_table_to_name():
    """
    Drops and recreates the ideas table to use 'name' as the foreign key instead of 'user_id'.
    WARNING: This will delete all existing ideas data.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        DROP TABLE IF EXISTS ideas;
        CREATE TABLE ideas (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL REFERENCES users(name) ON DELETE CASCADE,
            model_type TEXT NOT NULL,
            category TEXT NOT NULL,
            scope TEXT NOT NULL,
            keyword TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX idx_ideas_name ON ideas(name);
        CREATE INDEX idx_ideas_created_at ON ideas(created_at);
    ''')
    conn.commit()
    cursor.close()
    conn.close()
    print("Ideas table migrated to use 'name' as foreign key.")

if __name__ == "__main__":
    # Initialize the table first
    print("Initializing ideas table...")
    init_ideas_table()
    
    # Example usage for testing
    model_type = "gemini"
    category = "Technology"
    scope = "Trending Now"
    keyword = "AI"
    num_ideas = 5
    name = "usr_test123"  # Replace with actual user name from your users table

    ideas, storage_message, export_info = generate_ideas_and_store_postgres(
        model_type, category, scope, keyword, num_ideas, name, export_formats=["csv", "json", "excel"]
    )
    
    # Check if user exists
    if ideas is None:
        print(f"Error: {storage_message}")
        print("Please use a valid user name that exists in the database.")
    else:
        print("Ideas generated and stored:")
        for idea in ideas:
            print(f"- {idea.get('title', '')}: {idea.get('description', '')}")
        
        print(f"\nStorage: {storage_message}")
        
        if export_info:
            print(f"\nExport info:")
            if "csv" in export_info:
                print(f"CSV: {export_info['csv']['filepath']}")
            if "json" in export_info:
                print(f"JSON: {export_info['json']['filepath']}")
            if "excel" in export_info:
                print(f"Excel: {export_info['excel']['filepath']}")
        
        # Show user stats
        print(f"\nUser '{name}' statistics:")
        stats = get_user_stats(name)
        print(f"User: {stats['user_info']['firstName']} {stats['user_info']['lastName']}")
        print(f"Email: {stats['user_info']['email']}")
        print(f"Total ideas: {stats['total_ideas']}")
        print(f"Ideas by category: {stats['ideas_by_category']}")
        print(f"Last activity: {stats['last_activity']}")
        
        # Show recent ideas
        print(f"\nRecent ideas for '{name}':")
        recent_ideas = get_user_ideas_from_postgres(name, limit=3)
        for idea in recent_ideas:
            print(f"- {idea['title']} ({idea['category']})")
        
        # Show all users with ideas
        print(f"\nAll users with ideas:")
        users_with_ideas = get_all_users_with_ideas()
        for user in users_with_ideas:
            print(f"- {user['firstName']} {user['lastName']}: {user['idea_count']} ideas") 