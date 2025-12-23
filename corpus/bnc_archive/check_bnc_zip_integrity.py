import zipfile

def verify_zip_integrity(file_path):
    print(f"Checking integrity of {file_path}...")
    try:
        with zipfile.ZipFile(file_path, 'r') as zf:
            # testzip() returns the name of the first corrupt file it finds,
            # or None if all files are fine.
            bad_file = zf.testzip()
            if bad_file:
                print(f"CORRUPT: First error found in file: {bad_file}")
            else:
                print("SUCCESS: Zip file integrity verified. No errors found.")
    except zipfile.BadZipFile:
        print("ERROR: The file is not a zip file or is severely corrupted.")

verify_zip_integrity("bnc_xml_edition.zip")