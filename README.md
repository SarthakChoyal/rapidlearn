# Rapid Learn 🚀

Rapid Learn is an AI-powered learning assistant that helps you quickly understand YouTube videos through summaries and interactive quizzes.

## Features ✨

- **Video Summaries**: Get concise, well-structured summaries of YouTube videos
- **Custom Quizzes**: Generate interactive quizzes from any video or text content
- **User Profiles**: Save your summaries and track your learning progress
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## Getting Started 🌟

### Prerequisites
- Python 3.8 or higher
- Internet connection
- YouTube video URL
- Groq API Key (Free)

### Setting Up Groq API Key
1. Visit [Groq](https://groq.com/) and create a free account
2. Navigate to API Keys in your Groq console
3. Generate a new API key
4. Go to the `.env` file in the project directory
5. Add your API key to the `.env` file:
   ```
   GROQ_API_KEY=your_api_key_here
   ```

### Installation

#### Windows
1. Clone this repository
2. Set up your Groq API key as described above
3. Double-click `rapidlearn.bat`
4. Open your browser and go to `http://localhost:5000`

#### macOS/Linux
1. Clone this repository
2. Set up your Groq API key as described above
3. Make the script executable:
   ```bash
   chmod +x rapidlearn.sh
   ```
4. Run the script:
   ```bash
   ./rapidlearn.sh
   ```
5. Open your browser and go to `http://localhost:5000`

## How to Use 📚

1. **Create an Account**: Sign up with your email and password. Or simply sign in with the username "Admin" and password "admin".
2. **Generate Summaries**: 
   - Paste a YouTube URL
   - Click "Generate Summary"
   - Get an AI-generated summary of the video content
3. **Create Quizzes**:
   - Use the Custom Quiz feature
   - Enter any topic or paste content
   - Get interactive quizzes to test your knowledge

## Technologies Used 🛠️

- Flask (Python web framework)
- SQLite (Database)
- Groq API (AI processing)
- YouTube Transcript API (Python framework)
- Bootstrap (Frontend styling)

## Contributing 🤝

Contributions are welcome! Feel free to submit issues and pull requests.

## Author ✍️

Created by [Sarthak Choyal](https://github.com/SarthakChoyal)

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details. 
