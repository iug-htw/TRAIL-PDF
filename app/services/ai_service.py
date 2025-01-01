import os
import requests
import time
import csv
from flask import current_app
from app.services.image_service import encode_image
from app.utils.prompts import PROMPTS


def save_usage_to_csv(usage_info, filename="token_usage.csv"):
    """
    Saves token usage information to a CSV file.

    :param usage_info: Dictionary containing token usage data.
    :type usage_info: dict
    :param filename: The name of the CSV file to save the data in, defaults to "token_usage.csv".
    :type filename: str, optional
    :returns: None
    """
    # Get the directory for saving token usage logs from the app's configuration
    LOG_DIR = current_app.config['TOKEN_USAGE_DIR']
    os.makedirs(LOG_DIR, exist_ok=True)  # Ensure the directory exists

    filepath = os.path.join(LOG_DIR, filename)
    file_exists = os.path.isfile(filepath)
    with open(filepath, "a", newline='') as csvfile:
        fieldnames = ['prompt_tokens', 'completion_tokens', 'total_tokens']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')

        if not file_exists:
            writer.writeheader()  # Write the header only if the file doesn't exist

        writer.writerow(usage_info)


def send_image_to_ai(image_path, chosen_prompt):
    """
    Sends an image to the AI service and returns the generated text.

    - Encodes the image to a Base64 string.
    - Prepares and sends a request to the AI service with the encoded image.

    :param image_path: The file path to the image.
    :type image_path: str
    :param chosen_prompt: The key for the prompt text from the PROMPTS dictionary.
    :type chosen_prompt: str
    :returns: The generated text from the AI or an error message.
    :rtype: str
    """
    base64_image = encode_image(image_path)
    image_url = f"data:image/jpeg;base64,{base64_image}"

    prompt_text = PROMPTS.get(chosen_prompt)

    if prompt_text is None:
        current_app.logger.error(f"Unsupported language choice: {chosen_prompt}")
        return f"Error processing image. Unsupported language choice: {chosen_prompt}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {current_app.config['OPENAI_API_KEY']}"
    }

    if chosen_prompt == 'spell_check':
        # Special handling for spell check prompt
        with open(image_path, 'r') as file:
            text_content = file.read()
        payload = {
            "model": current_app.config['GPT_MODEL'],
            "messages": [
                {
                    "role": "user",
                    "content": prompt_text + "\n\n" + text_content
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.2
        }
    else:
        payload = {
            "model": current_app.config['GPT_MODEL'],
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.2
        }

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        if response.status_code == 200:
            response_json = response.json()
            text_content = response_json['choices'][0]['message']['content'] if response_json.get('choices') else ''
            usage_info = response_json.get('usage', {})

            save_usage_to_csv(usage_info)  # Save the token usage to a CSV file

            return text_content
        else:
            current_app.logger.error(
                f"Error from GPT API: Status Code {response.status_code}, Response: {response.text}")
            return f"Error processing image. API response status: {response.status_code}"
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Request to GPT API failed: {e}")
        return f"Error processing image. Exception: {e}"


def process_images_with_ai(images, chosen_prompt):
    """
    Processes a list of images with the AI service and returns the generated texts.

    - Iterates over the list of images, sending each to the AI service.
    - Waits 2 seconds between each image processing to avoid rate limiting.
    - Logs the progress and appends each generated text to the results list.

    :param images: List of file paths to the images.
    :type images: list of str
    :param chosen_prompt: The key for the prompt text from the PROMPTS dictionary.
    :type chosen_prompt: str
    :returns: A list of texts generated by the AI service for each image.
    :rtype: list of str
    """
    texts = []
    for i, image in enumerate(images):
        if i > 0:
            time.sleep(2)
        current_app.logger.info(f"Processing image {image} on page {i + 1}")

        text = send_image_to_ai(image, chosen_prompt)

        current_app.logger.info(f"Received text: {text}")
        texts.append(text)
    return texts
