import requests
from pathlib import Path

def download_bnc_corpus(url, output_path):
    # Stream the request to avoid loading 538MB into memory at once
    with requests.get(url, stream=True) as response:
        # Check if the request was successful
        response.raise_for_status()

        # Get total file size from headers (if available)
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192  # 8 KB chunks
        downloaded = 0

        print(f"Starting download to: {output_path}")

        with open(output_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    file.write(chunk)
                    downloaded += len(chunk)

                    # Simple progress update
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.2f}% ({downloaded // (1024*1024)} MB)", end="")

        print(f"\nDownload complete! File saved to {output_path}")

# Configuration
BNC_URL = "https://llds.ling-phil.ox.ac.uk/llds/xmlui/bitstream/handle/20.500.14106/2554/2554.zip?sequence=4&isAllowed=y"
SAVE_AS = "bnc_xml_edition.zip"

if __name__ == "__main__":
    try:
        download_bnc_corpus(BNC_URL, SAVE_AS)
    except Exception as e:
        print(f"An error occurred: {e}")