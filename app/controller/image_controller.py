from flask import Blueprint, request, jsonify, render_template, current_app
from app.services.ai_service import send_image_to_ai
from app.services.image_service import save_image, delete_image, is_valid_image
from app.utils.prompts import PROMPTS

image_bp = Blueprint('image', __name__)


@image_bp.route('/image-upload')
def image_upload():
    return render_template('image_upload.html')


@image_bp.route('/process-image', methods=['POST'])
def process_image():
    TEMP_IMAGE_PATH = current_app.config['TEMP_IMAGE_PATH']
    if 'image' in request.files:
        image = request.files['image']
        prompt_type = request.form.get('prompt', 'standard')
        language = request.form.get('language', 'german')

        current_app.logger.info(f"Received image: {image.filename}")

        if not is_valid_image(image):
            return jsonify({"error": "Invalid image uploaded"}), 400

        # Determine the prompt key based on language and prompt type
        prompt_key = f"{prompt_type}_{language}"
        if prompt_key not in PROMPTS:
            current_app.logger.error(f"Unsupported prompt key: {prompt_key}")
            return jsonify({"error": f"Unsupported language or prompt type: {prompt_key}"}), 400

        image_path = save_image(image, TEMP_IMAGE_PATH)
        alt_text = send_image_to_ai(image_path, prompt_key)
        delete_image(image_path)

        return jsonify(alt_text=alt_text)
    else:
        current_app.logger.error("No image uploaded")
        return jsonify({"error": "No image uploaded"}), 400
