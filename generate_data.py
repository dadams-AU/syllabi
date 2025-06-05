import os
import json

def generate_syllabus_data():
    syllabi = []
    # Define course directories based on the ls output
    # These are the top-level directories that seem to contain courses
    course_root_dirs = [
        "CRJU_POSC 320 Intro PA",
        "POSC 315 Intro Policy",
        "POSC 428",
        "POSC 509 MPA Foundations",
        "POSC 521 MPA Capstone",
        "POSC 588 Collab Gov"
    ]

    # Try to infer a more descriptive title from the directory name
    def get_course_title(course_dir_name):
        if "Intro PA" in course_dir_name:
            return "Introduction to Public Administration"
        if "Intro Policy" in course_dir_name:
            return "Introduction to Public Policy"
        if "Enviro Policy" in course_dir_name or "POSC 428" in course_dir_name: # POSC 428 seems to be Environmental Policy
             return "Environmental Policy"
        if "MPA Foundations" in course_dir_name:
            return "MPA Foundations"
        if "MPA Capstone" in course_dir_name:
            return "MPA Capstone"
        if "Collab Gov" in course_dir_name:
            return "Collaborative Governance"
        # Fallback, try to use parts of the dir name
        parts = course_dir_name.split(" ")
        # Attempt to find a course code like POSC_315 or CRJU_POSC_320
        code_like = [p for p in parts if "_" in p or p.isupper()]
        if code_like:
            return " ".join(parts[len(code_like):]).replace("_", " ").strip() + " Syllabus"
        return course_dir_name.replace("_", " ") # Default if no better title found


    for course_dir in course_root_dirs:
        if not os.path.isdir(course_dir):
            print(f"Warning: Directory {course_dir} not found. Skipping.")
            continue

        course_code_parts = course_dir.split(" ")[0].split("_") # E.g. "CRJU_POSC" -> ["CRJU", "POSC"], "POSC" -> ["POSC"]
        base_course_code = "_".join(course_code_parts) # e.g. CRJU_POSC, POSC

        # Iterate through subdirectories which often represent terms
        for term_dir in os.listdir(course_dir):
            term_path = os.path.join(course_dir, term_dir)
            if os.path.isdir(term_path):
                # Skip common non-term directories like "asynch proposal" or "hybrid proposal" or "POSC 521 as Hybrid"
                if "proposal" in term_dir.lower() or "hybrid" in term_dir.lower() or "bibliography" in term_dir.lower():
                    continue

                term_name = term_dir.replace("_", " ").replace(" Intersession", " Intersession") # "2023-24 Intersession"

                # Look for PDF files
                for filename in os.listdir(term_path):
                    if filename.endswith(".pdf"):
                        pdf_path = os.path.join(term_path, filename)
                        # Try to infer a specific course code and title from filename if possible, else use base
                        file_course_code = base_course_code
                        if len(course_code_parts) > 1 and course_code_parts[0] in filename and course_code_parts[1] in filename: # e.g. CRJU and POSC in filename
                             file_course_code = f"{course_code_parts[0]}_{course_code_parts[1]}"
                        elif course_code_parts[0] in filename:
                             file_course_code = course_code_parts[0]

                        # Extract number from filename if possible, e.g. CRJU-POSC_320.pdf -> 320
                        num_match = [char for char in filename.split('.')[0] if char.isdigit()]
                        if num_match:
                            course_num = "".join(num_match)[:3] # Take first 3 digits found
                            if not any(char.isdigit() for char in file_course_code): # Add number if not already part of base_code
                                file_course_code_suffix = file_course_code.split("_")[-1] # POSC or 320
                                if not any(char.isdigit() for char in file_course_code_suffix):
                                     file_course_code = f"{file_course_code}_{course_num}" # POSC_320
                                elif file_course_code_suffix != course_num : # If POSC_315 but file is POSC_320.pdf
                                     file_course_code = f"{file_course_code.split('_')[0]}_{course_num}"


                        # Refine course code: ensure it doesn't just become "320"
                        if file_course_code.isdigit(): # if only numbers were extracted
                            file_course_code = f"{base_course_code.split('_')[0]} {file_course_code}" # e.g. POSC 320
                        else: # POSC_320 -> POSC 320
                            file_course_code = file_course_code.replace("_", " ")


                        file_formats = ["PDF"]
                        tex_path_no_ext = os.path.splitext(pdf_path)[0]
                        if os.path.exists(tex_path_no_ext + ".tex"):
                            file_formats.append("TEX")

                        # Tags: from course code parts
                        tags = list(set(part for part in file_course_code.split(" ") if not part.isdigit() and len(part) > 1)) # POSC, CRJU
                        # Add level tag
                        level_match = [char for char in file_course_code if char.isdigit()]
                        if level_match:
                            level = level_match[0] + "00" # e.g., '3' -> '300'
                            tags.append(f"{level}-level")


                        syllabi.append({
                            "courseCode": file_course_code.upper(), # e.g. POSC 320
                            "title": get_course_title(course_dir), # Generic title based on root folder
                            "term": term_name,
                            "fileFormats": file_formats,
                            "path": pdf_path,
                            "tags": sorted(list(set(tags))), # Unique sorted tags
                            "description": f"Syllabus for {file_course_code.upper()} - {term_name}."
                        })
            # Check for PDF files directly under course_dir (e.g. POSC 428)
            elif term_dir.endswith(".pdf"): # term_dir here is actually a filename
                pdf_path = os.path.join(course_dir, term_dir)
                file_course_code = base_course_code # POSC

                num_match = [char for char in term_dir.split('.')[0] if char.isdigit()]
                if num_match:
                    course_num = "".join(num_match)[:3]
                    if not any(char.isdigit() for char in file_course_code):
                         file_course_code = f"{file_course_code} {course_num}" # POSC 428
                    elif file_course_code.split(" ")[-1] != course_num :
                         file_course_code = f"{file_course_code.split(' ')[0]} {course_num}"
                else: # If no number in filename, but dir is POSC 428
                    dir_num_match = [char for char in course_dir if char.isdigit()]
                    if dir_num_match:
                        file_course_code = f"{file_course_code} {''.join(dir_num_match)}"


                file_formats = ["PDF"]
                tex_path_no_ext = os.path.splitext(pdf_path)[0]
                if os.path.exists(tex_path_no_ext + ".tex"):
                    file_formats.append("TEX")

                tags = list(set(part for part in file_course_code.split(" ") if not part.isdigit() and len(part) > 1))
                level_match = [char for char in file_course_code if char.isdigit()]
                if level_match:
                    level = level_match[0] + "00"
                    tags.append(f"{level}-level")

                # Term for these files is less clear, use a placeholder or try to infer if needed.
                # For now, using directory name as a proxy if it implies a term, or a generic one.
                inferred_term = "Undated" # Placeholder
                # Example: if course_dir was "POSC 428 Spring 24", could parse "Spring 24"
                # This part is tricky without consistent naming.

                syllabi.append({
                    "courseCode": file_course_code.upper(),
                    "title": get_course_title(course_dir),
                    "term": inferred_term, # Needs better inference if possible
                    "fileFormats": file_formats,
                    "path": pdf_path,
                    "tags": sorted(list(set(tags))),
                    "description": f"Syllabus for {file_course_code.upper()}."
                })


    # Remove exact duplicates based on path
    unique_syllabi = []
    seen_paths = set()
    for syllabus in syllabi:
        if syllabus["path"] not in seen_paths:
            unique_syllabi.append(syllabus)
            seen_paths.add(syllabus["path"])

    return unique_syllabi

# Generate the data
new_syllabi_data = generate_syllabus_data()

# Write to data/syllabi.json
# Ensure the /data directory exists (it should from previous steps)
output_path = "data/syllabi.json"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, "w") as f:
    json.dump(new_syllabi_data, f, indent=2)

print(f"Successfully generated {len(new_syllabi_data)} syllabus entries in {output_path}")
for entry in new_syllabi_data[:3]: # Print a few samples
    print(entry)

# Verify by listing files in data directory
print("\nFiles in data directory:")
for item in os.listdir("data"):
    print(item)
