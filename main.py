import os
import shutil
from bible_import import main as download_bible
from convert import traverse_directory

download_folder = "./download"
output_folder = "./output"

def delete_all_folders(folder):
    for item in os.listdir(folder):
        item_path = os.path.join(folder, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)

def main(download_folder=download_folder):
    translations = download_bible(download_folder, output_folder)
    
    if not translations:
        return "No translations were downloaded."
    
    # Handle both single translation (string) and multiple translations (list)
    if isinstance(translations, str):
        translations = [translations]
    
    successful_downloads = []
    for translation in translations:
        print(f"\nConverting {translation} to JSON...")
        traverse_directory(download_folder, translation, output_type='single')
        successful_downloads.append(f"{download_folder}/{translation}.json")
    
    delete_all_folders(download_folder)

    if len(successful_downloads) == 1:
        return f"Successfully Downloaded & Saved to {successful_downloads[0]}"
    else:
        return f"Successfully Downloaded & Saved {len(successful_downloads)} translations:\n" + "\n".join(successful_downloads)


if __name__ == "__main__":
    successful = main()
    print(successful)