from flask import Blueprint, current_app, request, redirect, url_for, flash, send_file
import os
from app.services.pdf_service import extract_text_from_pdf
from app.services.ai_service import send_image_to_ai
from app.utils.helpers import save_text_to_file, save_corrected_text

spell_check_bp = Blueprint('spell_check', __name__)

@spell_check_bp.route('/spell_check/<filename>', methods=['POST'])
def spell_check(filename):
    """
    Checks the spelling of the text extracted from a PDF.

    - Logs the start of the spell check process.
    - Extracts text from the PDF, sends it to the AI service for spell checking, and saves the corrected text.
    - Handles and logs errors during the spell check process.

    :param filename: The name of the PDF file to check.
    :type filename: str
    :returns:
        Response: A response that initiates the download of the corrected text file.
        Redirect: Redirects to the file details page if an error occurs.
    :rtype: flask.Response
    """
    current_app.logger.info(f"Starting spell check for {filename}")
    file_path = os.path.join(current_app.config['UPLOAD_PATH'], filename)

    try:
        # Extract text from PDF
        text = extract_text_from_pdf(file_path)
        text_file_path = save_text_to_file(text, filename)

        # Send text to AI for spell checking
        corrected_text = send_image_to_ai(text_file_path, 'spell_check')

        # Save corrected text
        corrected_text_file_path = save_corrected_text(corrected_text, filename)

        flash('Spell check completed successfully.')
        current_app.logger.info(f"Spell check completed for {filename}")
        return send_file(corrected_text_file_path, as_attachment=True)

    except Exception as e:
        flash(f'Error during spell check: {e}')
        current_app.logger.error(f"Error during spell check for {filename}: {e}")
        return redirect(url_for('file.file_details', filename=filename))
    finally:
        os.remove(text_file_path)
        os.remove(corrected_text_file_path)
