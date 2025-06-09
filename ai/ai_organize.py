import os
import shutil
import google.generativeai as genai

class AIFileOrganizer:
    """
    A class to organize files into directories using an AI model (Gemini).
    """
    def __init__(self, gemini_api_key: str):
        """
        Initializes the AIFileOrganizer with the Gemini API key.

        Args:
            gemini_api_key (str): The API key for Google Gemini.
        """
        genai.configure(api_key=gemini_api_key)
        # use gemini-2.0-flash
        self.model = genai.GenerativeModel('gemini-2.0-flash') 

    def _get_file_preview(self, file_path: str, max_chars: int = 1000) -> str:
        """
        Reads a preview of the file content.

        Args:
            file_path (str): The path to the file.
            max_chars (int): The maximum number of characters to read for the preview.

        Returns:
            str: A preview of the file content, or an empty string if an error occurs.
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(max_chars)
        except Exception as e:
            print(f"\n\n\nError reading file {file_path}: {e}")
            return ""

    def _get_subfolders(self, current_dir: str) -> list[str]:
        """
        Gets a list of subfolders in the given directory.

        Args:
            current_dir (str): The path to the directory to scan.

        Returns:
            list[str]: A list of subfolder names. Returns an empty list on permission errors.
        """
        try:
            entries = os.listdir(current_dir)
            subfolders = [entry for entry in entries if os.path.isdir(os.path.join(current_dir, entry))]
            return subfolders
        except PermissionError:
            print(f"\n\n\nPermission denied for directory: {current_dir}")
            return []
        except Exception as e:
            print(f"\n\n\nError listing subfolders in {current_dir}: {e}")
            return []

    def _ask_gemini_for_decision(self, file_name: str, content_preview: str, current_path: str, subfolders: list[str]) -> str | None:
        """
        Asks the Gemini model for a decision on where to place the file or where to navigate next.

        Args:
            file_name (str): The name of the file.
            content_preview (str): A preview of the file's content.
            current_path (str): The current directory path being evaluated.
            subfolders (list[str]): A list of subfolders in the current directory.

        Returns:
            str | None: The AI's decision ('SELECT CURRENT', a subfolder name, 'STOP'), 
                        or None if an error occurs or the decision is invalid.
        """
        prompt_parts = [
            "You are an AI file organizer. You MUST respond ONLY with 'SELECT CURRENT', a folder name, or 'STOP'.",
            f"File name: '{file_name}'",
            f"Content preview: '{content_preview}'",
            "Task: Determine file placement location",
            f"Current path: '{current_path}'"
        ]

        if not subfolders:
            prompt_parts.append("There are no subfolders in this directory.")
            prompt_parts.append(f"Is '{current_path}' the correct destination for this file?")
            prompt_parts.append("Respond with 'SELECT CURRENT' if it is, or 'STOP' if it is not and there are no other options.")
        else:
            subfolders_string = ", ".join([f"'{f}'" for f in subfolders])
            prompt_parts.append(f"The subfolders in this directory are: {subfolders_string}")
            prompt_parts.append("Which of these options is best?")
            prompt_parts.append(f"1. Place the file in the current directory ('{current_path}'). (Respond with: 'SELECT CURRENT')")
            prompt_parts.append(f"2. Go into one of the subfolders to look for a better location. (Respond with the subfolder name from the list: {subfolders_string})")
            prompt_parts.append("Your response should be either 'SELECT CURRENT' or the name of ONE subfolder from the list.")
        
        prompt = "".join(prompt_parts)
        # Add overall folder structure context (up to 20 folders)
        try:
            all_folders = self._get_folder_structure(self.start_directory)
            if all_folders:
                folders_str = ", ".join([f"'{f}'" for f in all_folders])
                prompt += f"\nOverall folder structure (up to 20): {folders_str}"
        except Exception:
            pass

        try:
            response = self.model.generate_content(prompt)
            decision = response.text.strip()
            print(f"\n\n\nGemini decision: {decision}")
            # Validate decision
            if decision == "SELECT CURRENT" or decision in subfolders:
                return decision
            elif not subfolders and decision == "STOP":  # 'STOP' valid only if no subfolders
                return decision
            else:
                print(f"\n\n\nGemini returned an unexpected or invalid decision: '{decision}'.")
                print(f"\n\n\nValid options were 'SELECT CURRENT', one of {subfolders}, or 'STOP' (if no subfolders).")
                return "STOP"
        except Exception as e:
            print(f"\n\n\nError communicating with Gemini: {e}")
            return None

    def _get_folder_structure(self, current_dir: str, max_folders: int = 20) -> list[str]:
        """
        Retrieves up to max_folders folder paths under current_dir for context.

        Args:
            current_dir (str): The path to the directory to scan.
            max_folders (int): The maximum number of folder paths to retrieve.

        Returns:
            list[str]: A list of folder paths relative to current_dir.
        """
        folders = []
        for root, dirs, _ in os.walk(current_dir):
            for d in dirs:
                # store paths relative to current_dir
                rel = os.path.relpath(os.path.join(root, d), start=current_dir)
                folders.append(rel)
                if len(folders) >= max_folders:
                    return folders
        return folders

    def organize_file(self, source_file_path: str, start_directory: str = "C:/") -> str | None:
        """
        Organizes a file into a directory structure starting from start_directory using AI.

        Args:
            source_file_path (str): The path to the file to be organized.
            start_directory (str): The root directory to start the organization process.
                                   WARNING: Starting at "C:/" can be very slow, resource-intensive,
                                   and may encounter permission issues.
                                   Consider using a more specific starting point like user's 
                                   Documents, Downloads, or a project folder.

        Returns:
            str: The path where the file was moved, or None if organization failed or was stopped.
        """
        if not os.path.isfile(source_file_path):
            print(f"\n\n\nError: Source file '{source_file_path}' not found.")
            return None

        file_name = os.path.basename(source_file_path)
        content_preview = self._get_file_preview(source_file_path)

        if not content_preview and not file_name:
            print("\n\n\nFile is empty or has no name. Cannot organize.")
            return None

        start_dir_abs = os.path.abspath(start_directory)
        self.start_directory = start_dir_abs  # store for overall folder structure context
        current_path = start_dir_abs
        # Limit depth to prevent infinite loops or excessive navigation
        max_depth = 10  # Adjust as needed
        current_depth = 0

        visited_paths = set() # To avoid cycles if AI makes repetitive suggestions

        while current_depth < max_depth:
            if current_path in visited_paths:
                print(f"\n\n\nRe-visiting path '{current_path}'. Stopping to prevent loop.")
                return None
            visited_paths.add(current_path)

            print(f"\n\n\nCurrently evaluating: {current_path}")
            
            try:
                subfolders = self._get_subfolders(current_path)
            except Exception as e: # Catch any unexpected errors during subfolder listing
                print(f"\n\n\nCritical error listing subfolders for {current_path}: {e}. Stopping.")
                return None

            decision = self._ask_gemini_for_decision(file_name, content_preview, current_path, subfolders)

            if decision is None:
                print("\n\n\nFailed to get a decision from AI. Stopping organization.")
                return None
            
            if decision == "SELECT CURRENT":
                destination_path = os.path.join(current_path, file_name)
                # Instead of moving, just return the proposed path
                print(f"\n\n\nAI proposes to place file in: {destination_path}")
                return destination_path
            elif decision == "STOP":
                print(f"\n\n\nAI suggested to stop organization at '{current_path}'.")
                return None
            elif decision in subfolders:
                next_path_candidate = os.path.join(current_path, decision)
                # Basic check to ensure the path is still somewhat reasonable (e.g. not excessively long)
                if len(next_path_candidate) > 250 : # Arbitrary limit for path length
                    print(f"\n\n\nPath {next_path_candidate} is too long. Stopping.")
                    return None
                current_path = next_path_candidate
                current_depth += 1
            else:
                # This case should ideally be handled by the validation in _ask_gemini_for_decision
                # which now defaults to "STOP" for unrecognized responses.
                print(f"\n\n\nAI suggested an invalid folder or action '{decision}'. Stopping organization.")
                return None
        
        print(f"\n\n\nReached maximum depth ({max_depth}) at '{current_path}'. Stopping organization.")
        return None

# Example Usage (for testing purposes, can be removed or commented out)
if __name__ == "__main__":
    # IMPORTANT: Set your Gemini API Key as an environment variable or pass it directly.
    # For security, using an environment variable is preferred.
    gemini_api_key = "AIzaSyCw4U0MHSGJBOrK0fA9aGzQwokdg0dbOhQ" # Replace with your actual key or os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        print("\n\n\nPlease set the GEMINI_API_KEY environment variable or provide it directly in the script.")
    else:
        organizer = AIFileOrganizer(gemini_api_key=gemini_api_key)

        # --- Test Setup ---
        test_file_name = "dummy_financial_report_2024_Q3.txt"
        # Create in current dir, outside TestOrg initially
        original_test_file_path = os.path.join(os.getcwd(), test_file_name) 
        
        with open(original_test_file_path, "w", encoding="utf-8") as f:
            f.write("This is a financial report for Q3 2024. It contains sales figures and projections for the company.")

        base_test_dir = os.path.join(os.getcwd(), "TestOrg")
        reports_dir = os.path.join(base_test_dir, "Documents", "Financial", "Reports_2024")
        pictures_dir = os.path.join(base_test_dir, "Media", "Pictures")
        
        os.makedirs(reports_dir, exist_ok=True)
        os.makedirs(pictures_dir, exist_ok=True)
        # --- End Test Setup ---

        print(f"\n\n\nAttempting to organize file: {original_test_file_path}")
        print(f"\n\n\nStarting organization scan from: {base_test_dir}")

        # Get the proposed destination from the organizer
        proposed_destination = organizer.organize_file(original_test_file_path, start_directory=base_test_dir)

        actual_file_location = original_test_file_path # Assume not moved initially

        if proposed_destination:
            print(f"\n\n\nAI suggests moving the file to: {proposed_destination}")
            # Simulate user confirmation / proceed with move
            print(f"\n\n\nUser confirms. Moving '{original_test_file_path}' to '{proposed_destination}'...")
            try:
                # Ensure the destination directory exists
                os.makedirs(os.path.dirname(proposed_destination), exist_ok=True)
                shutil.move(original_test_file_path, proposed_destination)
                print(f"\n\n\nFile moved successfully.")
                actual_file_location = proposed_destination
            except Exception as e:
                print(f"\n\n\nError moving file to {proposed_destination}: {e}")
                # File remains at original_test_file_path if move fails
        else:
            print(f"\n\n\nAI-driven organization did not yield a destination or was stopped. File not moved by the script.")

        print(f"\n\n\n--- Final Status ---")
        if os.path.exists(actual_file_location):
            if actual_file_location == original_test_file_path:
                print(f"\n\n\nFile '{test_file_name}' remains at its original location: {actual_file_location}")
            else:
                print(f"\n\n\nFile '{test_file_name}' was organized and moved to: {actual_file_location}")
        else:
            # This case implies the original file was moved, but then actual_file_location might be wrong,
            # or original file was deleted before it could be moved.
            print(f"\n\n\nFile '{test_file_name}' is not at the expected final location ({actual_file_location}) or original location.")


        # --- Test Cleanup (Optional) ---
        print(f"\n\n\nCleaning up test directory: {base_test_dir}")
        shutil.rmtree(base_test_dir, ignore_errors=True) # This will remove TestOrg and its contents (including the moved file if it's there)
        
        # Clean up the original dummy file if it still exists (e.g., if it was never moved or move failed)
        if os.path.exists(original_test_file_path): 
            print(f"\n\n\nCleaning up original test file: {original_test_file_path}")
            os.remove(original_test_file_path)
        elif actual_file_location != original_test_file_path and os.path.exists(actual_file_location):
            # This case is if the file was moved outside base_test_dir and cleanup of base_test_dir didn't get it.
            # However, with current logic, proposed_destination should be within base_test_dir.
            # For safety, if it was moved and not cleaned by rmtree, try to clean it.
            # This part is less likely to be hit with the current test setup.
            if not actual_file_location.startswith(os.path.abspath(base_test_dir)):
                 print(f"\n\n\nCleaning up moved test file outside base_test_dir: {actual_file_location}")
                 os.remove(actual_file_location)
        # --- End Test Cleanup ---
