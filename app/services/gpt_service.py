import requests
import time
from flask import current_app
from app.services.image_service import encode_image
from app.utils.prompts import PROMPTS


def send_image_to_gpt(image_path, chosen_language):
    base64_image = encode_image(image_path)
    image_url = f"data:image/jpeg;base64,{base64_image}"

    prompt_text = PROMPTS.get(chosen_language)

    if prompt_text is None:
        current_app.logger.error(f"Unsupported language choice: {chosen_language}")
        return f"Error processing image. Unsupported language choice: {chosen_language}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {current_app.config['OPENAI_API_KEY']}"
    }

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
            return text_content
        else:
            current_app.logger.error(
                f"Error from GPT API: Status Code {response.status_code}, Response: {response.text}")
            return f"Error processing image. API response status: {response.status_code}"
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Request to GPT API failed: {e}")
        return f"Error processing image. Exception: {e}"


def process_images_with_gpt(images, chosen_language):
    texts = []
    for i, image in enumerate(images):
        if i > 0:
            time.sleep(6)
        current_app.logger.info(f"Processing image {image} on page {i + 1}")

        text = send_image_to_gpt(image, chosen_language)

        current_app.logger.info(f"Received text: {text}")
        texts.append(text)
    return texts