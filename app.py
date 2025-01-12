from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
from flask_login import LoginManager, login_required, current_user
from youtube_transcript_api import YouTubeTranscriptApi
import groq
import os
from dotenv import load_dotenv
import re
from models import db, User, Summary
from auth import auth as auth_blueprint
import markdown

load_dotenv()

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

# Add markdown filter
@app.template_filter('markdown')
def markdown_filter(text):
    return markdown.markdown(text) if text else ''

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Register blueprints
app.register_blueprint(auth_blueprint)

# Initialize Groq client
groq_client = groq.Groq(api_key=os.getenv('GROQ_API_KEY'))

def extract_video_id(url):
    # Extract video ID from different types of YouTube URLs
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_transcript(video_id):
    try:
        # List of English language codes to try
        english_codes = ['en', 'en-GB', 'en-US', 'en-CA', 'en-AU', 'en-NZ', 'en-IE', 'en-ZA']
        
        # Try each language code until we find a transcript
        for lang_code in english_codes:
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang_code])
                transcript_text = ' '.join([item['text'] for item in transcript_list])
                return transcript_text
            except Exception:
                continue  # Try next language code if this one fails
        
        # If we get here, try to get any available transcript and translate it to English
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcript_list.find_transcript(['en'])  # Try to find English first
            
            if not transcript:
                # If no English transcript found, get the first available one and translate it
                transcript = transcript_list.find_manually_created_transcript()
                transcript = transcript.translate('en')
            
            transcript_text = ' '.join([item['text'] for item in transcript.fetch()])
            return transcript_text
            
        except Exception as e:
            return f"Could not get transcript. Error: {str(e)}"
            
    except Exception as e:
        return str(e)

def summarize_text(text):
    try:
        user_prompt = f"""You are a precise educational summarizer. Your task is to summarize ONLY the content from the provided transcript.
        Do not add any external information or make assumptions.

        Rules:
        1. ONLY use information directly stated in the transcript
        2. Do not mention machine learning unless it's specifically discussed in the transcript
        3. If you're unsure about a topic, only include what's explicitly stated
        4. Focus on the actual content of this specific video
        5. Write for GCSE/A-level students

        Here is the transcript to summarize:
        ```
        {text}
        ```

        Format your response with:
        - ### Overview (2-3 sentences about what THIS video covers)
        - ### Key Topics (only topics actually discussed)
        - ### Detailed Explanation (using only information from the transcript)
        - ### Summary (key points from THIS video only)

        Use:
        - **bold** for key terms that appear in the transcript
        - Bullet points for lists
        - *italics* for emphasis on words from the transcript
        """

        completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise educational summarizer. Only use information directly from the provided transcript. Do not add external information or make assumptions."
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            model="mixtral-8x7b-32768",
            temperature=0.1,  # Lower temperature for more focused output
            max_tokens=2048
        )
        
        return completion.choices[0].message.content
    except Exception as e:
        return str(e)

def generate_quiz(text):
    try:
        # Validate input
        if not text or len(text.strip()) < 50:
            return "Error: Transcript is too short to generate a meaningful quiz"

        quiz_prompt = f"""Create a multiple-choice quiz based on this transcript.

        Transcript:
        ```
        {text}
        ```

        Rules:
        1. Create exactly 5 questions
        2. Each question must be directly based on the transcript content
        3. Make questions clear and straightforward
        4. All answer options must be plausible
        5. Include one correct answer and three incorrect answers
        6. Use simple language suitable for students

        Format each question exactly like this:

        ### Quiz

        1. [Clear question about a specific fact from the transcript]
        - A) [Option]
        - B) [Option]
        - C) [Option]
        - D) [Option]

        ANSWER_START
        Correct: [Letter]
        Explanation: [Brief explanation from the transcript]
        ANSWER_END

        [Repeat format for all 5 questions]
        """

        completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a quiz generator. Create clear, factual questions based only on the provided transcript."
                },
                {
                    "role": "user",
                    "content": quiz_prompt
                }
            ],
            model="mixtral-8x7b-32768",
            temperature=0.3,  # Slightly higher for more variety in questions
            max_tokens=2048
        )
        
        quiz_response = completion.choices[0].message.content
        
        # Validate response
        if not quiz_response or len(quiz_response.strip()) < 50:
            raise Exception("Generated quiz is too short or empty")
            
        return quiz_response
        
    except Exception as e:
        return f"Error generating quiz: {str(e)}"

@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('index.html')
    return redirect(url_for('auth.login'))

@app.route('/profile')
@login_required
def profile():
    summaries = Summary.query.filter_by(user_id=current_user.id).order_by(Summary.created_at.desc()).all()
    return render_template('profile.html', summaries=summaries)

@app.route('/summarize', methods=['POST'])
@login_required
def summarize():
    try:
        data = request.get_json()
        video_url = data.get('video_url')
        
        video_id = extract_video_id(video_url)
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL'})
        
        transcript = get_transcript(video_id)
        if 'error' in transcript.lower():
            return jsonify({'error': transcript})
        
        summary = summarize_text(transcript)
        
        # Save summary to database
        new_summary = Summary(
            video_url=video_url,
            summary_text=summary,
            user_id=current_user.id
        )
        db.session.add(new_summary)
        db.session.commit()
        
        return jsonify({'summary': summary})
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/generate_quiz', methods=['POST'])
@login_required
def quiz():
    try:
        data = request.get_json()
        video_url = data.get('video_url')
        
        video_id = extract_video_id(video_url)
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL'})
        
        transcript = get_transcript(video_id)
        if 'error' in transcript.lower():
            return jsonify({'error': transcript})
            
        # Validate transcript
        if not transcript or len(transcript.strip()) < 50:
            return jsonify({'error': 'Transcript is too short or empty'})
            
        # Generate quiz with error handling
        try:
            quiz = generate_quiz(transcript)
            if not quiz or len(quiz.strip()) < 50:
                return jsonify({'error': 'Failed to generate a valid quiz'})
            return jsonify({'quiz': quiz})
        except Exception as e:
            print(f"Quiz generation error: {str(e)}")  # Debug print
            return jsonify({'error': f'Error generating quiz: {str(e)}'})
    
    except Exception as e:
        print(f"Route error: {str(e)}")  # Debug print
        return jsonify({'error': str(e)})

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/delete_summary/<int:summary_id>', methods=['DELETE'])
@login_required
def delete_summary(summary_id):
    try:
        summary = Summary.query.get_or_404(summary_id)
        
        # Check if the summary belongs to the current user
        if summary.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        db.session.delete(summary)
        db.session.commit()
        
        return jsonify({'message': 'Summary deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/custom_quiz')
@login_required
def custom_quiz_page():
    return render_template('custom_quiz.html')

@app.route('/generate_custom_quiz', methods=['POST'])
@login_required
def generate_custom_quiz():
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        question_count = int(data.get('question_count', 10))  # Convert to int
        
        # Validate question count
        if question_count < 5 or question_count > 20:
            return jsonify({'error': 'Question count must be between 5 and 20'})

        # Reduced minimum content length to 20 characters
        if not prompt or len(prompt.strip()) < 20:
            return jsonify({'error': 'Please enter some content to generate a quiz about'})

        quiz_prompt = f"""Create a multiple-choice quiz based on this content.

        Content:
        ```
        {prompt}
        ```

        Rules:
        1. Create exactly {question_count} questions
        2. Each question must be directly based on the provided content
        3. Make questions clear and straightforward
        4. All answer options must be plausible
        5. Include one correct answer and three incorrect answers
        6. Use simple language suitable for students
        7. Write for GCSE/A-level students
        8. There are different exam boards (Edexcel, AQA, OCR, etc.) so make sure you dont confuse them for other things
        9. Ensure the questions are relevent to the specification and not just some random question.

        Format each question exactly like this:

        ### Quiz

        1. [Clear question about a specific fact]
        - A) [Option]
        - B) [Option]
        - C) [Option]
        - D) [Option]

        ANSWER_START
        Correct: [Letter]
        Explanation: [Brief explanation why this is correct]
        ANSWER_END

        [Repeat format for all {question_count} questions]
        """

        completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a quiz generator. Create clear, factual questions based only on the provided content."
                },
                {
                    "role": "user",
                    "content": quiz_prompt
                }
            ],
            model="mixtral-8x7b-32768",
            temperature=0.3,  # Slightly higher for more variety in questions
            max_tokens=4096   # Increased for longer quizzes
        )

        quiz_response = completion.choices[0].message.content
        
        # Validate response
        if not quiz_response or len(quiz_response.strip()) < 50:
            raise Exception("Generated quiz is too short or empty")
            
        return jsonify({'quiz': quiz_response})
        
    except Exception as e:
        print(f"Error generating custom quiz: {str(e)}")  # For debugging
        return jsonify({'error': f'Error generating quiz: {str(e)}'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=False) 