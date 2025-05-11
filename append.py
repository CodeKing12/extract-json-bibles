import sqlite3
import json
import click
import unicodedata
from main import download_folder

def insert_bible_data(json_path, db_path, version, description=None):
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

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
                print(verse_str, text, chapter_str)
                verse = int(verse_str)
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
    conn.close()

if __name__ == '__main__':
    # version: str = click.prompt("What version are you trying to import? ")
    # version = version.upper()
    # description: str = click.prompt("What is the display name of this Bible? ")
    # db_path: str = click.prompt("Input the path of your database: ")

    for version, description in {
        "ampc": "Amplified Bible, Classic Edition",
        "nlt": "New Living Translation",
        "niv": "New International Version",
        "asv": "American Standard Version",
        "kjv": "King James Version",
        "nkjv": "New King James Version",
        "tlv": "Tree of Life Version",
    }.items():
        version = version.upper()
        print(version, description)
        insert_bible_data(
            json_path=f'{download_folder}/{version}.json',
            db_path='bibles.sqlite',
            version=version,
            description=description
        )