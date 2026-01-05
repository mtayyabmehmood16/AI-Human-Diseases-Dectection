from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from src.ai_client import AIClient
from src.matcher import DiseaseMatcher
import PIL.Image
import io
import base64
from flask_login import login_required, current_user
import os
import google.generativeai as genai
import speech_recognition as sr
from pydub import AudioSegment

main_bp = Blueprint('main', __name__)



@main_bp.route('/api/transcribe', methods=['POST'])
@login_required
def transcribe_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    recognizer = sr.Recognizer()
    
    try:
        # Save temp or process in memory
        # Web audio is often webm/ogg. SR needs WAV usually.
        # Use pydub to convert.
        audio_data = audio_file.read()
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_data))
        wav_io = io.BytesIO()
        audio_segment.export(wav_io, format="wav")
        wav_io.seek(0)
        
        with sr.AudioFile(wav_io) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
            return jsonify({'text': text})
            
    except Exception as e:
        print(f"Transcription error: {e}")
        return jsonify({'error': str(e)}), 500


# Initialize Matcher but load it lazily or globally
# For simplicity, we can have a global singleton here or better in a separate extensions file.
# We'll use a global variable here for now, mimicking app.py behavior.
matcher = DiseaseMatcher()

# CSV path will be loaded from config
def get_csv_path():
    """Get CSV path from Flask config or use default."""
    try:
        return current_app.config.get('DISEASE_CSV_PATH', 'data/diseases.csv')
    except RuntimeError:
        # Outside application context
        return os.environ.get('DISEASE_CSV', 'data/diseases.csv')

CSV_PATH = get_csv_path()
try:
    matcher.fit_from_csv(CSV_PATH)
except Exception as e:
    print(f"Matcher load error: {e}")

# Initialize AI client using configuration
def get_ai_client():
    """Get AI client instance with API key from config."""
    try:
        api_key = current_app.config.get('GEMINI_API_KEY')
        if not api_key:
            current_app.logger.warning("GEMINI_API_KEY not configured")
            return None
        return AIClient(api_key=api_key)
    except RuntimeError:
        # Outside application context, try environment variable
        api_key = os.environ.get('GEMINI_API_KEY')
        if api_key:
            return AIClient(api_key=api_key)
        return None

# Initialize global AI client
ai_client = get_ai_client()
 

@main_bp.route('/', methods=['GET'])
def index():
    loaded = getattr(matcher, 'csv_path', None)
    count = len(matcher.df) if getattr(matcher, 'df', None) is not None else 0
    return render_template('index.html', loaded=loaded, count=count)

@main_bp.route('/skin', methods=['GET', 'POST'])
def skin_analysis():
    if request.method == 'GET':
        return render_template('skin.html')
    
    # POST
    image_file = request.files.get('image')
    image_data = request.form.get('image_data') # From camera capture
    
    if not image_file and not image_data:
        flash('Please upload an image or capture a photo.', 'warning')
        return redirect(url_for('main.skin_analysis'))

    try:
        img = None
        if image_file:
            img = PIL.Image.open(image_file)
        elif image_data:
            # data:image/jpeg;base64,...
            header, encoded = image_data.split(",", 1)
            data = base64.b64decode(encoded)
            img = PIL.Image.open(io.BytesIO(data))
        
        if img:
            prompt = """
            Analyze this image of a skin condition. Act as a dermatologist.
            1. Describe what you see (color, texture, pattern).
            2. Suggest 3 possible causes (differential diagnosis).
            3. Provide home care recommendations.
            4. State clearly: "DISCLAIMER: This is an AI analysis and not a medical diagnosis. Consult a doctor."
            
            Format response in Markdown (Bold, Lists).
            """
            response = ai_client.generate_content([prompt, img])
            return render_template('skin.html', result=response, image_data=image_data)
            
    except Exception as e:
        flash(f'Error analyzing image: {e}', 'danger')
        return redirect(url_for('main.skin_analysis'))

    return render_template('skin.html')

@main_bp.route('/match', methods=['GET', 'POST'])
def match():
    if request.method == 'GET':
        return render_template('match_form.html')

    symptoms = request.form.get('symptoms', '')
    if not symptoms.strip():
        flash('Please enter symptoms.', 'warning')
        return redirect(url_for('main.match'))
        
    results = []
    try:
        results = matcher.match(symptoms, top_k=10, threshold=0.0)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        
    # Gemini
    prompt = f"""
    Based on these symptoms: '{symptoms}', suggest possible diseases that match and provide health recommendations.
    
    Please format your response using Markdown:
    - Use **Bold** for emphasis.
    - Use lists for recommendations.
    - Create clear sections like '## Possible Causes' and '## Recommendations'.
    """
    gemini_response = ai_client.generate_content(prompt)

    return render_template('results.html', query=symptoms, results=results, gemini_response=gemini_response)

@main_bp.route('/find', methods=['GET', 'POST'])
def find():
    if request.method == 'GET':
        return render_template('find_form.html')
        
    name = request.form.get('dname', '')
    if not name.strip():
        return redirect(url_for('main.find'))
        
    results = matcher.find_by_name(name, exact=False, limit=50)
    
    gemini_response = None
    prompt = f"""
    Provide comprehensive information about the disease '{name}'.
    
    Please format your response using Markdown:
    - Use headings (##) for sections like 'Symptoms', 'Causes', 'Treatments'.
    - Use bullet points for lists.
    - Make it easy to read.
    """
    gemini_response = ai_client.generate_content(prompt)

    return render_template('find_results.html', name=name, results=results, gemini_response=gemini_response)

@main_bp.route('/status')
def status():
    loaded = getattr(matcher, 'csv_path', None)
    count = len(matcher.df) if getattr(matcher, 'df', None) is not None else 0
    return render_template('status.html', loaded=loaded, count=count)

@main_bp.route('/reload', methods=['POST'])
def reload():
    path = request.form.get('reload_path', '') or CSV_PATH
    try:
        matcher.fit_from_csv(path)
        flash(f'Reloaded CSV: {path}', 'success')
    except Exception as e:
        flash(f'Failed to reload CSV: {e}', 'danger')
    return redirect(url_for('main.index'))

@main_bp.route('/chat', methods=['GET', 'POST'])
@main_bp.route('/chat.html', methods=['GET', 'POST']) # Alias for compatibility
@main_bp.route('/chat', methods=['GET', 'POST'])
@main_bp.route('/chat.html', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
         user_input = request.form.get('message', '')
         if user_input:
             try:
                 # 1. Analyze Intention & Extract Symptoms
                 # 1. Analyze Intention & Extract Symptoms
                 prompt = f"""
                 Act as a medical assistant. User says: "{user_input}"
                 Task: 
                 1. Identify if the user is describing symptoms.
                 2. If yes, extract keywords as a comma-separated list.
                 3. Provide a helpful, empathetic response (max 50 words). Format the response using Markdown (bold key terms).
                 
                 Output format: JSON
                 {{
                    "symptoms": ["fever", "cough"] or [],
                    "response": "**Response:** Text here with **markdown**..."
                 }}
                 """
                 # Use global ai_client
                 resp_text = ai_client.generate_content(prompt)
                 
                 import json
                 cleaned_text = resp_text.strip()
                 if cleaned_text.startswith('```json'):
                     cleaned_text = cleaned_text[7:-3]
                 elif cleaned_text.startswith('```'): # Handle cases where json tag might be missing but backticks exist
                     cleaned_text = cleaned_text[3:-3]
                 
                 try:
                     data = json.loads(cleaned_text)
                 except:
                     # Fallback if JSON parsing fails but we got text
                     data = {"symptoms": [], "response": resp_text}
                 
                 matches = []
                 if 'symptoms' in data and data['symptoms']:
                     symptom_str = " ".join(data['symptoms'])
                     matches = matcher.match(symptom_str, top_k=3)
                     # Serialize matches for JSON
                     matches = [{'name': m['name'], 'probability': m['probability'], 'precautions': m['precautions']} for m in matches]
                 
                 return jsonify({'response': data.get('response', resp_text), 'matches': matches})
             except Exception as e:
                 print(f"Chat error detailed: {e}")
                 import traceback
                 traceback.print_exc()
                 return jsonify({'response': f"AI Error: {str(e)}", 'matches': []})
    return render_template('chat.html')

