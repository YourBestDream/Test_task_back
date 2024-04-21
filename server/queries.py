import os
import shutil
import time
import traceback
from werkzeug.utils import secure_filename
import datetime

from flask import Blueprint, jsonify, request
from langchain.document_loaders.generic import GenericLoader
from langchain.document_loaders.parsers.audio import OpenAIWhisperParserLocal
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import User, History
from . import db

queries = Blueprint('queries', __name__)

whisper_parser = OpenAIWhisperParserLocal(device="gpu", lang_model='openai/whisper-small')


@queries.route('/speech2text', methods=['POST'])
def query():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        package_dir = os.path.dirname(os.path.abspath(__file__))
        sub_dir = "Audio"
        save_dir = os.path.join(package_dir, sub_dir)

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(save_dir, filename)
        file.save(filepath)
        print(filepath)
        # Setup GenericLoader with the correct parser for audio files
        audio_loader = GenericLoader.from_filesystem(
            path=filepath,
            parser=whisper_parser
        )
        
        # Load and process the audio file
        start = time.time()
        result = next(audio_loader.lazy_load())
        end = time.time()
        print(end-start)
        print(result.page_content)

        return jsonify({
            'message': 'File uploaded and processed successfully',
            'transcription': result.page_content
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

    finally:
        shutil.rmtree(save_dir)

@queries.route('/update-requests-and-history', methods=['POST'])
@jwt_required()
def update_requests_and_history():
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    new_count = data.get('newCount')
    transcription = data.get('transcription')

    # Update the user's remaining requests
    user.remaining_requests = new_count

    # Add new history entry
    history_entry = History(user_id=user.id, text=transcription, timestamp=datetime.datetime.utcnow())
    db.session.add(history_entry)

    try:
        db.session.commit()
        return jsonify({"message": "User data updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@queries.route('/retrieve', methods=['GET'])
@jwt_required()
def retrieve():
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    history_items = [{
        "text": history_item.text,
        "timestamp": history_item.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    } for history_item in user.history.all()]

    return jsonify({
        "remaining_requests": user.remaining_requests,
        "history": history_items
    })