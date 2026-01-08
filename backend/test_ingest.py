import json
import time
import os
from datetime import datetime

def create_test_ingest_file(text_content):
    """Create a test JSON file in the ingest directory"""
    ingest_dir = "ingest"
    if not os.path.exists(ingest_dir):
        os.makedirs(ingest_dir)
    
    # Create JSON data
    data = {
        "text": text_content,
        "timestamp": datetime.now().isoformat(),
        "source": "test"
    }
    
    # Create filename with timestamp
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}.txt"
    filepath = os.path.join(ingest_dir, filename)
    
    # Write JSON to file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Created test file: {filepath}")
    print(f"Content: {text_content}")
    print("Note: After processing, the file will be renamed to .old suffix")
    return filepath

if __name__ == "__main__":
    print("=== Test Ingest File Creator ===")
    print("This script creates test JSON files in the ingest directory")
    print()
    
    # Test messages
    test_messages = [
        "Hello Cursor AI! This is a test message.",
        "Can you help me with Python programming?",
        "Please analyze this code and suggest improvements.",
        "What are the best practices for error handling?",
        "I need help with database optimization."
    ]
    
    print("Available test messages:")
    for i, msg in enumerate(test_messages, 1):
        print(f"{i}. {msg}")
    
    print("\nEnter message number (1-5) or 'q' to quit:")
    
    while True:
        try:
            choice = input("Choice: ").strip()
            if choice.lower() == 'q':
                break
            elif choice.isdigit():
                msg_num = int(choice)
                if 1 <= msg_num <= len(test_messages):
                    create_test_ingest_file(test_messages[msg_num - 1])
                    print("Test file created! Check if copychat.py processes it.")
                else:
                    print("Invalid choice. Please enter 1-5 or 'q'.")
            else:
                print("Invalid input. Please enter a number or 'q'.")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("Goodbye!")
