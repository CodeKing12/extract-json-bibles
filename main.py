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
    translation = download_bible(download_folder, output_folder)
    traverse_directory(download_folder, translation, output_type='single')
    delete_all_folders(download_folder)

    return f"Successfully Downloaded & Saved to {download_folder}/{translation}.json"


if __name__ == "__main__":
    successful = main()
    print(successful)