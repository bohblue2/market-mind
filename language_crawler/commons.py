import os
import requests

def download_pdf(url, save_path):
    # Send a GET request to the URL
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Ensure the save_path directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Write the content to a file
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"PDF successfully downloaded and saved to {save_path}")
    else:
        print(f"Failed to download PDF. Status code: {response.status_code}")