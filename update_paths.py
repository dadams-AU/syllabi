import json
import os
import urllib.parse

# Configuration
json_file_path = "data/syllabi.json"
github_user = "dadams-AU"
github_repo = "syllabi"
github_branch = "main" # Assuming main, user can specify if different
base_raw_url = f"https://raw.githubusercontent.com/{github_user}/{github_repo}/{github_branch}/"

# Read existing JSON data
try:
    with open(json_file_path, 'r') as f:
        syllabi_data = json.load(f)
except FileNotFoundError:
    print(f"Error: {json_file_path} not found. Please ensure the file exists and was pulled.")
    exit(1)
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from {json_file_path}.")
    exit(1)

updated_syllabi = []
paths_changed_count = 0
paths_already_urls_count = 0
path_errors = []

for syllabus in syllabi_data:
    original_path = syllabus.get("path", "")
    new_path_for_url_construction = original_path # Start with original for URL construction logic

    if not original_path:
        path_errors.append(f"Missing path for courseCode: {syllabus.get('courseCode', 'N/A')}")
        updated_syllabi.append(syllabus) # Keep entry as is
        continue

    # Check if it's already a full raw GitHub URL
    if original_path.startswith("https://raw.githubusercontent.com/"):
        paths_already_urls_count += 1
        # Optional: ensure it points to the correct repo/branch if desired, for now, assume it's correct
        updated_syllabi.append(syllabus)
        continue

    # Ensure path for URL construction points to a .pdf, not .tex
    if original_path.endswith(".tex"):
        new_path_for_url_construction = original_path[:-4] + ".pdf"
        print(f"Path for URL construction changed from .tex to .pdf: {original_path} -> {new_path_for_url_construction}")
    elif not original_path.endswith(".pdf"):
        # If it's not .tex and not .pdf, this is unexpected.
        print(f"Warning: Path does not end with .pdf or .tex: {original_path}. Will proceed to make URL, but ensure it's a valid file path.")
        # new_path_for_url_construction remains original_path here
        pass

    # URL encode the path components (excluding slashes)
    # Split path, encode parts, then rejoin
    path_parts = new_path_for_url_construction.split('/')
    encoded_path_parts = [urllib.parse.quote(part) for part in path_parts]
    encoded_local_path = "/".join(encoded_path_parts)

    # Construct the full raw GitHub URL
    full_raw_url = base_raw_url + encoded_local_path

    # Update the path in the syllabus entry
    syllabus["path"] = full_raw_url
    if original_path != full_raw_url: # Check if actual change occurred to the path string
        paths_changed_count +=1

    updated_syllabi.append(syllabus)

# Write updated data back to JSON file
with open(json_file_path, 'w') as f:
    json.dump(updated_syllabi, f, indent=2)

print(f"\nUpdated {json_file_path} successfully.")
print(f"Paths converted to full raw GitHub URLs or extension potentially adjusted for URL: {paths_changed_count}")
print(f"Paths already full URLs (skipped conversion): {paths_already_urls_count}")
if path_errors:
    print("\nErrors encountered:")
    for error in path_errors:
        print(f"- {error}")

# Print a few samples
print("\nSample updated entries:")
for entry in updated_syllabi[:2]:
    print(json.dumps(entry, indent=2))
