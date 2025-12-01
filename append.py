import sqlite3
import json
import click
import unicodedata
import os
from requests import get

download_folder = "./download"

# API headers for Bible.com
headers = {
    "Referer": "https://bible.com/",
    "Origin": "https://bible.com",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
}

def get_all_bibles_metadata(language="eng"):
    """Fetch all available bibles for a language and return a dict keyed by abbreviation."""
    bibles_resp = get(f"https://www.bible.com/api/bible/versions?language_tag={language}&type=all", headers=headers)
    bible_list_json = bibles_resp.json()
    available_bibles = bible_list_json["response"]["data"]["versions"]
    
    # Create a lookup dict by local_abbreviation (case-insensitive)
    bible_lookup = {}
    for bible in available_bibles:
        abbr = bible.get('local_abbreviation', '').upper()
        if abbr:
            bible_lookup[abbr] = {
                'id': bible.get('id'),
                'title': bible.get('local_title', bible.get('title', '')),
                'abbreviation': bible.get('local_abbreviation', bible.get('abbreviation', ''))
            }
    return bible_lookup

def insert_bible_data(json_path, db_path, version, description=None):
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Insert Bible version
        cursor.execute('''
            INSERT OR IGNORE INTO bibles (version, description)
            VALUES (?, ?)
        ''', (version, description))
        
        # Get bible_id
        cursor.execute('SELECT id FROM bibles WHERE version = ?', (version,))
        bible_id = cursor.fetchone()[0]

        # Load JSON data
        with open(json_path, 'r', encoding='utf-8') as f:
            bible_data = json.load(f)

        # Prepare insert statements
        insert_book = '''
            INSERT OR IGNORE INTO books (book_name) VALUES (?)
        '''
        
        insert_scripture = '''
            INSERT OR IGNORE INTO scriptures 
            (bible_id, book_id, book_name, version, chapter, verse, text)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''

        # Process each book
        for book_name, chapters in bible_data.items():
            # Insert book
            cursor.execute(insert_book, (book_name,))
            cursor.execute('SELECT id FROM books WHERE book_name = ?', (book_name,))
            book_id = cursor.fetchone()[0]

            # Process chapters
            for chapter_str, verses in chapters.items():
                chapter = int(chapter_str)
                
                # Process verses
                for verse_str, text in verses.items():
                    # Keep verse as string to handle ranges like "1-4" and suffixes like "6b"
                    verse = verse_str
                    clean_text = unicodedata.normalize('NFC', text.strip())

                    cursor.execute(insert_scripture, (
                        bible_id,
                        book_id,
                        book_name,
                        version,
                        chapter,
                        verse,
                        clean_text
                    ))

        conn.commit()
    finally:
        conn.close()

def get_json_files_in_folder(folder):
    """Get all JSON files in the download folder."""
    json_files = []
    if os.path.exists(folder):
        for file in os.listdir(folder):
            if file.endswith('.json'):
                json_files.append(file)
    return json_files

if __name__ == '__main__':
    db_path = click.prompt("Input the path of your database", default='bibles.sqlite')
    language = click.prompt("Language code for fetching Bible metadata", default='eng')
    
    # Get all JSON files in the download folder
    json_files = get_json_files_in_folder(download_folder)
    
    if not json_files:
        print(f"No JSON files found in {download_folder}")
        exit(1)
    
    print(f"Found {len(json_files)} Bible file(s) to import:")
    for f in json_files:
        print(f"  - {f}")
    
    # Fetch Bible metadata from API
    print(f"\nFetching Bible metadata for language: {language}...")
    bible_lookup = get_all_bibles_metadata(language)
    print(f"Found {len(bible_lookup)} available Bibles in the API\n")
    
    # Process each JSON file
    for json_file in json_files:
        version = json_file.replace('.json', '').upper()
        json_path = os.path.join(download_folder, json_file)
        
        # Try to get description from API, fallback to version name
        bible_info = bible_lookup.get(version, {})
        description = bible_info.get('title', version)
        
        print(f"Importing {version}: {description}")
        
        try:
            insert_bible_data(
                json_path=json_path,
                db_path=db_path,
                version=version,
                description=description
            )
            print(f"  ✓ Successfully imported {version}")
        except Exception as e:
            print(f"  ✗ Failed to import {version}: {e}")
    
    print("\nDone!")