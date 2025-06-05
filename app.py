import streamlit as st
import pdfplumber
from openai import OpenAI
import os
import json
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key="") ##add openai API key here

def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file"""
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def analyze_resume(resume_text):
    """Analyze resume and extract all information at once"""
    system_prompt = """
    Analyze the resume and provide the following information in JSON format:
    {
        "basic_info": {
            "full_name": "",
            "email": "",
            "phone": "",
            "current_position": "",
            "location": ""
        },
        "professional_info": {
            "years_of_experience": "",
            "tech_stack": [],
            "key_achievements": []
        }
    }
    Keep the analysis focused and concise.
    """
    
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": resume_text}
            ],
            temperature=0.7
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        st.error(f"Error analyzing resume: {str(e)}")
        return None

def generate_mcq_questions(resume_text, analysis):
    """Generate MCQ questions based on the resume analysis"""
    system_prompt = """
    Create 10 Multiple Choice Questions (MCQs) that test the candidate's knowledge in their core tech stack and abilities.
    Focus on their technical skills and experience level.
    
    Format as JSON:
    {
        "questions": [
            {
                "question": "Technical question based on their experience",
                "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
                "correct_answer": "A",
                "explanation": "Brief explanation of the correct answer"
            }
        ]
    }
    """
    
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Resume Text: {resume_text}\nAnalysis: {json.dumps(analysis)}"}
            ],
            temperature=0.7
        )
        return completion.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating questions: {str(e)}")
        return None

def generate_interview_summary(questions, answers, profile_info):
    """Generate a summary of the interview performance"""
    # Calculate score
    correct_count = sum(1 for q, a in zip(questions, answers) if q['correct_answer'] == a)
    
    # Prepare summary prompt
    summary_prompt = f"""
    Create a concise performance summary (exactly 50 words) for a candidate who scored {correct_count}/10.
    Their profile: {json.dumps(profile_info)}
    Their answers: {json.dumps(list(zip([q['question'] for q in questions], answers)))}
    
    Focus on:
    1. Strong areas
    2. Areas for improvement
    3. One key recommendation
    """
    
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": summary_prompt},
                {"role": "user", "content": "Generate the summary."}
            ],
            temperature=0.7
        )
        return correct_count, completion.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating summary: {str(e)}")
        return correct_count, "Unable to generate summary."

def display_chat_message(text, is_user=False):
    """Display a chat message"""
    message_class = "user-message" if is_user else "bot-message"
    st.markdown(f"""
        <div class="chat-message {message_class}">
            {text}
        </div>
    """, unsafe_allow_html=True)

def display_question(question, options, question_number, total_questions):
    """Display a question in chat format"""
    st.markdown(f"""
        <div class="question-container fade-in">
            <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                <span>Question {question_number}/{total_questions}</span>
                <div class="progress-bar" style="width: 200px;">
                    <div class="progress-fill" style="width: {(question_number/total_questions)*100}%;"></div>
                </div>
            </div>
            <p style="font-size: 1.1rem; margin-bottom: 1rem;">{question}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Display options as radio buttons
    selected = st.radio(
        "Select your answer:",
        options,
        key=f"q_{question_number}",
        label_visibility="collapsed"
    )
    return selected

def display_loading_credentials():
    """Display a loading message for credentials"""
    with st.spinner("🔍 Extracting basic information..."):
        time.sleep(0.5)  # Brief pause for visual feedback

def display_loading_analysis():
    """Display a loading message for detailed analysis"""
    with st.spinner("📊 Performing detailed analysis and generating questions..."):
        time.sleep(0.5)  # Brief pause for visual feedback

def display_user_info_card(user_info):
    """Display user information in a card format"""
    st.markdown("""
        <style>
        .user-info-card {
            border: 1px solid #ddd;
            padding: 20px;
            border-radius: 10px;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .tech-stack-item {
            background-color: #e3f2fd;
            color: #1976d2;
            padding: 4px 8px;
            border-radius: 12px;
            display: inline-block;
            margin: 2px;
            font-size: 0.8em;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="user-info-card">', unsafe_allow_html=True)
    st.markdown("### 👤 Candidate Profile")
    
    if user_info.get("full_name"):
        st.markdown(f"**Name:** {user_info['full_name']}")
    if user_info.get("current_position"):
        st.markdown(f"**Current Position:** {user_info['current_position']}")
    if user_info.get("years_of_experience"):
        st.markdown(f"**Experience:** {user_info['years_of_experience']}")
    if user_info.get("email"):
        st.markdown(f"**Email:** {user_info['email']}")
    if user_info.get("phone"):
        st.markdown(f"**Phone:** {user_info['phone']}")
    if user_info.get("location"):
        st.markdown(f"**Location:** {user_info['location']}")
    
    if user_info.get("tech_stack"):
        st.markdown("**Tech Stack:**")
        tech_stack_html = ""
        for tech in user_info["tech_stack"]:
            tech_stack_html += f'<span class="tech-stack-item">{tech}</span> '
        st.markdown(tech_stack_html, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def set_custom_style():
    """Set custom styling for the entire application"""
    st.markdown("""
        <style>
        /* Main container styling */
        .main {
            padding: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        /* Upload container styling */
        .upload-container {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 20px;
            padding: 2rem;
            text-align: center;
            border: 2px dashed #dee2e6;
            margin: 2rem 0;
            transition: all 0.3s ease;
        }
        
        .upload-container:hover {
            border-color: #1a73e8;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        
        /* Chat interface styling */
        .chat-container {
            background: white;
            border-radius: 15px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            margin: 1rem 0;
            max-height: 600px;
            overflow-y: auto;
        }
        
        .chat-message {
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 15px;
            max-width: 80%;
        }
        
        .bot-message {
            background: #f8f9fa;
            margin-right: auto;
        }
        
        .user-message {
            background: #e3f2fd;
            margin-left: auto;
            text-align: right;
        }
        
        /* Question styling */
        .question-container {
            background: white;
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .option-button {
            width: 100%;
            padding: 1rem;
            margin: 0.5rem 0;
            border: 1px solid #dee2e6;
            border-radius: 10px;
            background: white;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .option-button:hover {
            background: #f8f9fa;
            border-color: #1a73e8;
        }
        
        .option-button.selected {
            background: #e3f2fd;
            border-color: #1a73e8;
            color: #1a73e8;
        }
        
        /* Progress bar */
        .progress-bar {
            height: 6px;
            background: #e9ecef;
            border-radius: 3px;
            margin: 1rem 0;
        }
        
        .progress-fill {
            height: 100%;
            background: #1a73e8;
            border-radius: 3px;
            transition: width 0.3s ease;
        }
        
        /* Summary styling */
        .summary-container {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border-radius: 15px;
            padding: 2rem;
            margin-top: 2rem;
            text-align: center;
        }
        
        .score-display {
            font-size: 3rem;
            font-weight: bold;
            color: #1a73e8;
            margin: 1rem 0;
        }
        
        /* Animation */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .fade-in {
            animation: fadeIn 0.5s ease-out;
        }
        </style>
    """, unsafe_allow_html=True)

def display_upload_section():
    """Display the file upload section with modern styling"""
    st.markdown("""
        <div class="upload-container fade-in">
            <h2>📄 Upload Your Resume</h2>
            <p style="color: #666; margin: 1rem 0;">
                Upload your PDF resume to begin the AI-powered interview process
            </p>
        </div>
    """, unsafe_allow_html=True)

def display_progress_steps(current_step):
    """Display progress steps indicator"""
    steps = ["Upload Resume", "Basic Info", "Analysis", "Interview"]
    st.markdown("""
        <div class="progress-indicator">
            {}
        </div>
    """.format(
        "".join([f'<div class="progress-dot{"" if i > current_step else " active"}"></div>' 
                 for i in range(len(steps))])
    ), unsafe_allow_html=True)

def display_profile_card(profile_data, is_basic=True):
    """Display profile information in a modern card layout"""
    st.markdown("""
        <div class="profile-card fade-in">
            <div class="profile-header">
                <h3>👤 {}</h3>
            </div>
    """.format("Basic Profile" if is_basic else "Complete Profile"), unsafe_allow_html=True)
    
    for key, value in profile_data.items():
        if key == "tech_stack" and value:
            st.markdown("**Technical Skills:**")
            tech_stack_html = ""
            for tech in value:
                tech_stack_html += f'<span class="tech-stack-item">{tech}</span> '
            st.markdown(tech_stack_html, unsafe_allow_html=True)
        elif value:
            st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")
    
    st.markdown("</div>", unsafe_allow_html=True)

def display_question_card(question_number, total_questions, question_text, options):
    """Display question in a modern card layout"""
    st.markdown(f"""
        <div class="question-card fade-in">
            <div class="question-header">
                <h3>Question {question_number}/{total_questions}</h3>
            </div>
            <p style="font-size: 1.1rem; margin: 1rem 0;">{question_text}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Display options with custom styling
    selected = st.radio(
        "Select your answer:",
        options,
        key=f"q_{question_number}",
        label_visibility="collapsed"
    )
    return selected

def main():
    st.set_page_config(page_title="AI Technical Interview", layout="wide")
    set_custom_style()
    
    # Initialize session state
    if 'phase' not in st.session_state:
        st.session_state.phase = 'upload'  # upload, interview, summary
        st.session_state.current_question = 0
        st.session_state.questions = None
        st.session_state.answers = []
        st.session_state.resume_analysis = None
        st.session_state.ready_for_next = True

    st.markdown("""
        <h1 style='text-align: center; margin-bottom: 2rem;'>
            🤖 AI Technical Interview Assistant
        </h1>
    """, unsafe_allow_html=True)

    if st.session_state.phase == 'upload':
        display_upload_section()
        uploaded_file = st.file_uploader("", type="pdf")
        
        if uploaded_file:
            with st.spinner("Analyzing your resume..."):
                resume_text = extract_text_from_pdf(uploaded_file)
                if resume_text:
                    analysis = analyze_resume(resume_text)
                    if analysis:
                        st.session_state.resume_analysis = analysis
                        # Generate questions based on analysis
                        questions = generate_mcq_questions(resume_text, analysis)
                        if questions:
                            st.session_state.questions = json.loads(questions)["questions"]
                            st.session_state.phase = 'interview'
                            st.rerun()

    elif st.session_state.phase == 'interview':
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        if st.session_state.current_question == 0:
            display_chat_message(
                "Hello! I'll be your technical interviewer today. I'll ask you 10 multiple choice questions based on your experience and technical skills. Let's begin!"
            )
        
        current_q = st.session_state.questions[st.session_state.current_question]
        
        if st.session_state.ready_for_next:
            selected = display_question(
                current_q['question'],
                current_q['options'],
                st.session_state.current_question + 1,
                10
            )
            
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                if st.button("Submit Answer", use_container_width=True):
                    selected_letter = chr(ord('A') + current_q['options'].index(selected))
                    st.session_state.answers.append(selected_letter)
                    st.session_state.ready_for_next = False
                    st.rerun()
        
        if not st.session_state.ready_for_next:
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                button_text = "Next Question →" if st.session_state.current_question < 9 else "Complete Interview"
                if st.button(button_text, use_container_width=True):
                    if st.session_state.current_question < 9:
                        st.session_state.current_question += 1
                        st.session_state.ready_for_next = True
                    else:
                        st.session_state.phase = 'summary'
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.phase == 'summary':
        score, summary = generate_interview_summary(
            st.session_state.questions,
            st.session_state.answers,
            st.session_state.resume_analysis['professional_info']
        )
        
        st.markdown("""
            <div class="summary-container fade-in">
                <h2>🎉 Interview Complete!</h2>
                <div class="score-display">{}/10</div>
                <div style="margin: 2rem 0;">{}</div>
                <div style="margin-top: 2rem;">
                    <button class="option-button" onclick="window.location.reload();">
                        Start New Interview
                    </button>
                </div>
            </div>
        """.format(score, summary), unsafe_allow_html=True)

if __name__ == "__main__":
    main()