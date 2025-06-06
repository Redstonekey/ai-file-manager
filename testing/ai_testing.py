# Testing script for AIFileOrganizer
import os
import sys
import time
import random
import tempfile
import shutil
import json
# Ensure ai_core module is importable
sys.path.append(os.path.dirname(__file__))
from ai_core import AIFileOrganizer

def generate_test_env(organizer, base_dir):
    """
    Use AI to generate a random folder structure and a test file.
    Returns the file path and expected destination path.
    """
    prompt = (
        "Generate a random folder structure (depth 2-3) for categorizing files, ensuring each folder has at least two subdirectories. "
        "RESPONSE MUST BE ONLY valid JSON with no extra text. "
        "Format: {'folders': ['path1', 'path2', ...], 'file': {'name': 'filename.ext', 'expected': 'pathN'}}"
    )
    response = organizer.model.generate_content(prompt)
    raw = response.text.strip()
    # Strip markdown code fences if present
    lines = raw.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    raw = "\n".join(lines).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print("AI response not valid JSON after stripping fences:\n", raw)
        raise
    # Create folders
    for folder in data['folders']:
        os.makedirs(os.path.join(base_dir, folder), exist_ok=True)
    # Create test file in base directory
    file_name = data['file']['name']
    file_path = os.path.join(base_dir, file_name)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"Content for {file_name}")
    # Compute expected absolute path for the file
    expected_rel = data['file']['expected']
    expected_abs = os.path.join(base_dir, expected_rel, file_name)
    return file_path, expected_abs

def run_tests(num_tests=50):
    gemini_api_key = "AIzaSyCw4U0MHSGJBOrK0fA9aGzQwokdg0dbOhQ"
    if not gemini_api_key:
        print("Please set the GEMINI_API_KEY environment variable.")
        sys.exit(1)
    organizer = AIFileOrganizer(gemini_api_key)
    results = []
    for i in range(num_tests):
        temp_dir = tempfile.mkdtemp(prefix="ai_test_")
        try:
            # Generate AI-driven test environment
            file_path, expected = generate_test_env(organizer, temp_dir)
            start = time.time()
            proposed = organizer.organize_file(file_path, start_directory=temp_dir)
            elapsed = time.time() - start
            # Check if the proposed path matches the AI-expected destination
            correct = bool(proposed) and os.path.normpath(proposed) == os.path.normpath(expected)
            results.append((correct, elapsed))
            print(f"Test {i+1}: expected={expected}, proposed={proposed}, correct={correct}, time={elapsed:.2f}s")
        except Exception as e:
            print(f"Test {i+1} failed with error: {e}")
            results.append((False, None))
        finally:
            shutil.rmtree(temp_dir)
    total = len(results)
    correct_count = sum(1 for r in results if r[0])
    times = [r[1] for r in results if r[1] is not None]
    avg_time = sum(times) / len(times) if times else 0
    print("\n\nSummary:")
    print(f"Total tests: {total}")
    print(f"Correct placements: {correct_count}")
    print(f"Precision: {correct_count/total:.2%}")
    print(f"Average time: {avg_time:.2f}s")

if __name__ == "__main__":
    run_tests(2)
