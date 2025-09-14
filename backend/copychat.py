import os
import json
import time
from send_to_cursor import find_and_paste


class IngestFileHandler:
    def __init__(self):
        self.ingest_dir = "ingest"
        
    def check_for_new_files(self):
        """Check for new files in the ingest directory"""
        if not os.path.exists(self.ingest_dir):
            return

        for filename in os.listdir(self.ingest_dir):
            if filename[-4:] == '.txt' :
                try:
                    file_path = os.path.join(self.ingest_dir, filename)
                    print(f"New file detected: {file_path}")
                    self.process_file(file_path)
                except Exception as e:
                    print(e)
    
    def process_file(self, file_path):
        """Process a new ingest file and paste text to Cursor AI"""
        try:
            # Read the JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # Parse JSON and extract text
            try:
                data = json.loads(content)
                text_to_paste = data.get('text', '')
                if not text_to_paste:
                    print(f"No 'text' field found in {file_path}")
                    return
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON from {file_path}: {e}")
                return
            
            print(f"Extracted text: {text_to_paste[:100]}...")
            
            # Find Cursor AI window and paste text
            if self.paste_to_cursor(text_to_paste):
                print("Text successfully pasted to Cursor AI")
                # Rename file to .old to mark as processed
                self.mark_file_as_processed(file_path)
            else:
                print("Failed to paste text to Cursor AI")
                
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    
    def mark_file_as_processed(self, file_path):
        """Rename file to .old to mark as processed"""
        try:
            old_file_path = file_path + '.old'
            os.rename(file_path, old_file_path)
            print(f"File marked as processed: {old_file_path}")
        except Exception as e:
            print(f"Error marking file as processed: {e}")
    
    
    def paste_to_cursor(self, text):
        """Paste text to Cursor AI window using external function"""
        try:
            return find_and_paste(text)
        except Exception as e:
            print(f"Error pasting to Cursor AI: {e}")
            return False


def monitor_ingest_directory():
    """Start monitoring the ingest directory with periodic polling"""
    ingest_dir = "ingest"
    
    # Create ingest directory if it doesn't exist
    if not os.path.exists(ingest_dir):
        os.makedirs(ingest_dir)
        print(f"Created directory: {ingest_dir}")
    
    # Set up file handler
    handler = IngestFileHandler()
    
    print(f"Starting to monitor directory: {os.path.abspath(ingest_dir)}")
    print("Checking for new files every 1 second...")
    print("Press Ctrl+C to stop monitoring...")
    
    try:
        while True:
            handler.check_for_new_files()
            time.sleep(0.2)  # Check every 1 second
    except KeyboardInterrupt:
        print("\nStopping monitor...")


def process_existing_files():
    """Process any existing files in the ingest directory"""
    ingest_dir = "ingest"
    if not os.path.exists(ingest_dir):
        return
    
    handler = IngestFileHandler()
    for filename in os.listdir(ingest_dir):
        if filename.endswith('.txt') and not filename.endswith('.old'):
            file_path = os.path.join(ingest_dir, filename)
            print(f"Processing existing file: {filename}")
            handler.process_file(file_path)


if __name__ == "__main__":
    print("=== Cursor AI Auto-Paste Monitor ===")
    print("This script monitors the ingest directory for new JSON files")
    print("and automatically pastes the 'text' field to Cursor AI")
    print("Using periodic polling every 1 second...")
    print()
    
    # Start monitoring for new files
    monitor_ingest_directory()
