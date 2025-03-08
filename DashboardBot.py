import streamlit as st
import csv
import os
import time
import datetime
from ollama import Client
import subprocess
import pandas as pd

# Configure Streamlit page
st.set_page_config(
    page_title="Sampri - Asisten Prodi Informatika UMM",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced styling with modern look and distinct chat bubbles
st.markdown("""
<style>
    /* Main container styling */
    .main {
        padding: 0rem 1rem;
        max-width: 1200px;
        margin: 0 auto;
        background-color: #1F2937; /* Dark background */
        color: white; /* Text color */
    }
    
    /* Body styling */
    body {
        background-color: #1F2937; /* Dark background - fixed to match main */
        color: white; /* Default text color */
    }
    
    /* Reset any background colors */
    .stApp {
        background-color: #1F2937; /* Dark background */
    }
    
    /* Header styling */
    .stTitle {
        color: #60A5FA; /* Light blue */
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Input field styling */
    .stTextInput>div>div>input {
        padding: 0.75rem;
        border-radius: 10px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 1px 3px rgba(255, 255, 255, 0.1);
        background-color: #374151; /* Darker input background */
        color: white; /* Input text color */
    }
    
    /* Chat container */
    .chat-container {
        margin-top: 2rem;
        padding: 1rem;
        border-radius: 10px;
        background-color: #2D3748; /* Darker chat background */
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Message styling */
    .chat-message {
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        display: flex;
        flex-direction: row;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        animation: fadeIn 0.5s;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* User message - distinct blue theme */
    .chat-message.user {
        background-color: #1E3A8A; /* Dark blue */
        border-left: 5px solid #3B82F6;
        margin-left: 2rem;
        margin-right: 0.5rem;
    }
    
    /* Assistant message - distinct green theme */
    .chat-message.assistant {
        background-color: #1F2937; /* Darker green */
        border-left: 5px solid #10B981;
        margin-right: 2rem;
        margin-left: 0.5rem;
    }
    
    /* Avatar styling */
    .chat-message .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
    }
    
    .user .avatar {
        background-color: #3B82F6;
        color: white;
    }
    
    .assistant .avatar {
        background-color: #10B981;
        color: white;
    }
    
    /* Message content */
    .chat-message .content {
        margin-left: 1rem;
        width: calc(100% - 40px);
    }
    
    /* Timestamp styling */
    .timestamp {
        font-size: 0.8rem;
        color: #9CA3AF; /* Light gray */
        margin-bottom: 0.5rem;
        font-style: italic;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #374151; /* Dark sidebar background */
        border-radius: 10px;
        padding: 1rem;
    }
    
    /* Subheader styling */
    .sidebar-subheader {
        color: #60A5FA; /* Light blue */
        font-weight: 600;
        border-bottom: 2px solid #E5E7EB;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    
    /* Input placeholder */
    .stChatInput {
        border-radius: 10px !important;
    }
    
    /* Button styling */
    .stButton>button {
        border-radius: 8px;
        background-color: #3B82F6;
        color: white;
        font-weight: 600;
        padding: 0.5rem 1rem;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #2563EB;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* DataFrame styling */
    .stDataFrame {
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    /* Loading animation */
    .stSpinner > div > div {
        border-color: #3B82F6 !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for chat history and CSV filename
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'csv_filename' not in st.session_state:
    default_path = os.path.join(os.getcwd(), "sampri_interactions.csv")
    st.session_state.csv_filename = default_path

# Initialize Ollama client
@st.cache_resource
def get_ollama_client():
    try:
        return Client(host='http://localhost:11434')
    except Exception as e:
        st.error(f"Failed to connect to Ollama server: {e}")
        return None

client = get_ollama_client()

def save_to_csv(question, answer, filename=None):
    """
    Save user interaction and AI response to CSV file with error handling
    """
    if filename is None:
        filename = st.session_state.csv_filename
    
    try:    
        # Create directory if it doesn't exist
        directory = os.path.dirname(filename)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        # Check if file exists
        file_exists = os.path.isfile(filename)
        
        # Timestamp for logging
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Open CSV file
        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['timestamp', 'question', 'response']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header if new file
            if not file_exists:
                writer.writeheader()
            
            # Write interaction data
            writer.writerow({
                'timestamp': timestamp,
                'question': question,
                'response': answer
            })
        
        return True, "Data saved successfully"
    except Exception as e:
        return False, f"Error saving data: {str(e)}"

def check_model_exists():
    """
    Check if Sampri model exists
    """
    if client is None:
        return False
        
    try:
        models = client.list()
        return any(model['name'] == 'sampri' for model in models['models'])
    except Exception:
        return False

def create_model():
    """
    Load Sampri model if not exists using the modelfile
    """
    if client is None:
        return False
        
    if not check_model_exists():
        with st.spinner("Model Sampri belum ditemukan. Memuat model dari modelfile..."):
            try:
                # Ensure modelfile exists
                modelfile_path = 'sampri.modelfile'
                if not os.path.exists(modelfile_path):
                    st.error(f"Error: File {modelfile_path} tidak ditemukan")
                    return False
                
                # Use command line to create model
                result = subprocess.run(['ollama', 'create', 'sampri', '-f', modelfile_path], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    st.success("Model Sampri berhasil dibuat!")
                    time.sleep(2)  # Give time to read success message
                    return True
                else:
                    st.error(f"Error: {result.stderr}")
                    return False
                    
            except Exception as e:
                st.error(f"Error saat membuat model: {e}")
                return False
    return True

# Function to display message in UI
def display_message(role, content, timestamp=None):
    avatar = "👤" if role == "user" else "🤖"
    message_class = "user" if role == "user" else "assistant"
    
    if timestamp is None:
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    
    with st.container():
        st.markdown(f"""
        <div class="chat-message {message_class}">
            <div class="avatar">{avatar}</div>
            <div class="content">
                <div class="timestamp">{timestamp}</div>
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)

# Display header with modern styling
st.markdown("<h1 style='text-align: center; color: #60A5FA;'>Sampri - Asisten Prodi Informatika UMM</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #9CA3AF; margin-bottom: 2rem;'>Asisten virtual yang dapat membantu Anda dengan informasi tentang Program Studi Informatika UMM</p>", unsafe_allow_html=True)

# Create two columns for the main layout
col1, col2 = st.columns([3, 1])

# Sidebar for configuration and history
with col2:
    st.markdown("<div class='sidebar-subheader'>Konfigurasi</div>", unsafe_allow_html=True)
    
    # CSV file configuration with error handling
    csv_path = st.text_input("Nama file CSV untuk penyimpanan", 
                            value=st.session_state.csv_filename)
    
    # Test button to verify CSV functionality
    if st.button("Test Simpan CSV"):
        success, message = save_to_csv("Test question", "Test response", csv_path)
        if success:
            st.success(message)
            st.session_state.csv_filename = csv_path
        else:
            st.error(message)
    
    # Display interaction history from CSV if exists with error handling
    st.markdown("<div class='sidebar-subheader'>Riwayat Interaksi</div>", unsafe_allow_html=True)
    
    try:
        if os.path.exists(st.session_state.csv_filename):
            try:
                df = pd.read_csv(st.session_state.csv_filename)
                with st.expander("Lihat Riwayat", expanded=False):
                    st.dataframe(df, use_container_width=True)
                
                # Option to download CSV
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Unduh Riwayat CSV",
                    csv_data,
                    os.path.basename(st.session_state.csv_filename),
                    "text/csv",
                    key='download-csv'
                )
            except Exception as e:
                st.error(f"Error membaca file CSV: {e}")
                st.info(f"Path yang dicoba: {os.path.abspath(st.session_state.csv_filename)}")
        else:
            st.info("File CSV belum ada. Akan dibuat saat pertama kali menyimpan chat.")
            st.info(f"Path yang akan digunakan: {os.path.abspath(st.session_state.csv_filename)}")
    except Exception as e:
        st.error(f"Error saat memeriksa file: {e}")
    
    # Add system information
    st.markdown("<div class='sidebar-subheader'>Info Sistem</div>", unsafe_allow_html=True)
    with st.expander("Status Sistem", expanded=False):
        st.info(f"Working directory: {os.getcwd()}")
        
        if client is None:
            st.error("Koneksi ke Ollama server gagal")
        elif check_model_exists():
            st.success("Model Sampri tersedia")
        else:
            st.warning("Model Sampri belum dimuat")

# Main chat area
with col1:
    # Create a container for the chat interface
    chat_container = st.container()
    
    with chat_container:
        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
        
        # Display saved messages from session history
        for message in st.session_state.messages:
            display_message(message["role"], message["content"], message.get("timestamp"))
        
        # If no messages yet, show a welcome message
        if not st.session_state.messages:
            welcome_message = """
            <p>Halo! Saya Sampri, asisten virtual Program Studi Informatika UMM. 
            Beberapa hal yang dapat saya bantu:</p>
            <ul>
                <li>Informasi tentang kurikulum dan mata kuliah</li>
                <li>Prosedur akademik di Prodi Informatika</li>
                <li>Kegiatan dan event prodi</li>
                <li>Informasi tentang laboratorium</li>
                <li>Dan banyak lagi!</li>
            </ul>
            <p>Silakan ajukan pertanyaan Anda.</p>
            """
            display_message("assistant", welcome_message)
            st.session_state.messages.append({
                "role": "assistant", 
                "content": welcome_message,
                "timestamp": datetime.datetime.now().strftime('%H:%M:%S')
            })
        
        st.markdown("</div>", unsafe_allow_html=True)

# Ensure model is available
model_ready = client is not None and create_model()

# Input area at the bottom
if model_ready:
    # Add some space before the input
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    # Use a container to position the input at the bottom
    with st.container():
        user_input = st.chat_input("Ketik pesan Anda di sini...")
        
        if user_input:
            # Display user message
            display_message("user", user_input)
            
            # Add to history
            timestamp = datetime.datetime.now().strftime('%H:%M:%S')
            st.session_state.messages.append({"role": "user", "content": user_input, "timestamp": timestamp})
            
            # Process response with loading indicator
            with st.spinner("Sampri sedang berpikir..."):
                try:
                    start_time = time.time()
                    response = client.chat(
                        model='sampri', 
                        messages=[{'role': 'user', 'content': user_input}]
                    )
                    end_time = time.time()
                    
                    # Get response from model
                    ai_response = response['message']['content']
                    
                    # Calculate response time
                    response_time = end_time - start_time
                    response_info = f"<small>Waktu respons: {response_time:.2f} detik</small>"
                    full_response = f"{ai_response}<br><br>{response_info}"
                    
                    # Display response
                    display_message("assistant", full_response)
                    
                    # Add to history
                    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": full_response,
                        "timestamp": timestamp
                    })
                    
                    # Save interaction to CSV with error handling
                    success, message = save_to_csv(user_input, ai_response)
                    if not success:
                        st.error(message)
                    
                except Exception as e:
                    error_message = f"Terjadi kesalahan: {str(e)}<br>Pastikan server Ollama berjalan dan model Sampri sudah dimuat."
                    display_message("assistant", error_message)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": error_message,
                        "timestamp": datetime.datetime.now().strftime('%H:%M:%S')
                    })
else:
    st.error("Tidak dapat memuat model Sampri. Pastikan file modelfile tersedia dan Ollama server berjalan.")

# Add footer
st.markdown("""
<div style='text-align: center; margin-top: 2rem; padding: 1rem; border-top: 1px solid #E5E7EB;'>
    <p style='color: #9CA3AF; font-size: 0.9rem;'>
        © 2025 Program Studi Informatika Universitas Muhammadiyah Malang
    </p>
</div>
""", unsafe_allow_html=True)