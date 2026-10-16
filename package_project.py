import os
import zipfile

def make_zip(output_filename="deepSheild_project.zip"):
    project_root = os.path.abspath(os.path.dirname(__file__))
    
    # Folders and file patterns to exclude from the ZIP
    exclude_dirs = {
        "node_modules", ".next", ".git", "__pycache__", 
        "venv", ".venv", "env", "cached_faces", ".cache", "xai_test", "xai_whatsapp", ".gemini"
    }
    exclude_extensions = {".pyc", ".tar", ".gz", ".archive"}
    
    print(f"Packaging deepSheild into {output_filename}...")
    file_count = 0
    total_size = 0
    
    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(project_root):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]
            
            for file in files:
                if file == output_filename or file.endswith(".zip"):
                    continue
                ext = os.path.splitext(file)[1].lower()
                if ext in exclude_extensions:
                    continue
                
                # Skip large temporary uploads to keep zip lightweight
                rel_path = os.path.relpath(os.path.join(root, file), project_root)
                if "uploads" in rel_path and file.endswith((".mp4", ".avi", ".mov", ".wav", ".mp3")):
                    continue
                    
                full_path = os.path.join(root, file)
                zipf.write(full_path, rel_path)
                file_count += 1
                total_size += os.path.getsize(full_path)
                
    zip_size_mb = os.path.getsize(output_filename) / (1024 * 1024)
    print("Packaging Complete!")
    print(f"File created: {output_filename}")
    print(f"Total files included: {file_count}")
    print(f"Final ZIP size: {zip_size_mb:.1f} MB")

if __name__ == "__main__":
    make_zip()
