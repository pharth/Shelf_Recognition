import streamlit as st
import requests
from PIL import Image
import io
import base64
import os
from dotenv import load_dotenv
from datetime import datetime
import time

# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()

# Mobile-optimized page config
st.set_page_config(
    page_title="Shelf Analytics",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile optimization
st.markdown("""
<style>
    /* Hide Streamlit branding and menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Mobile-first responsive design */
    .main-container {
        padding: 10px;
        max-width: 100%;
    }
    
    /* Header styling */
    .app-header {
        text-align: center;
        padding: 20px 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 20px 20px;
        color: white;
    }
    
    /* Camera frame styling */
    .camera-frame {
        border: 3px solid #4CAF50;
        border-radius: 15px;
        padding: 10px;
        margin: 20px 0;
        background: #f8f9fa;
        text-align: center;
    }
    
    /* Scanning animation */
    .scanning-text {
        color: #666;
        font-style: italic;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        border-radius: 25px;
        height: 50px;
        font-weight: 600;
        margin: 10px 0;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 10px 0;
        text-align: center;
    }
    
    /* Info section styling */
    .info-section {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 15px;
        margin: 15px 0;
        border-left: 4px solid #4CAF50;
    }
    
    /* Upload area */
    .upload-area {
        border: 2px dashed #ddd;
        border-radius: 15px;
        padding: 30px;
        text-align: center;
        margin: 20px 0;
        background: #fafafa;
    }
    
    /* Status indicators */
    .status-good { color: #4CAF50; font-weight: bold; }
    .status-moderate { color: #FF9800; font-weight: bold; }
    .status-poor { color: #f44336; font-weight: bold; }
    
    /* Mobile responsive adjustments */
    @media (max-width: 768px) {
        .main-container { padding: 5px; }
        .metric-card { margin: 5px 0; padding: 10px; }
    }
</style>
""", unsafe_allow_html=True)

# API endpoint configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Initialize session state
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'current_image' not in st.session_state:
    st.session_state.current_image = None
if 'scanning' not in st.session_state:
    st.session_state.scanning = False
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'output_image_data' not in st.session_state:
    st.session_state.output_image_data = None

# Configuration in sidebar (collapsed by default on mobile)
with st.sidebar:
    st.header("⚙️ Settings")
    api_url = st.text_input("API URL", value=API_BASE_URL)

ANALYTICS_ENDPOINT = f"{api_url}/api/analytics/analyze"
OUTPUT_IMAGE_ENDPOINT = f"{api_url}/api/analytics/output-image"

# ---------------------------
# Header
# ---------------------------
st.markdown("""
<div class="app-header">
    <h1 style="margin: 0; font-size: 24px;">📊 Shelf Analytics</h1>
    <p style="margin: 5px 0 0 0; opacity: 0.9;">Scan & Analyze Store Shelves</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------
# Navigation Tabs
# ---------------------------
tab1, tab2 = st.tabs(["📱 Scan Shelf", "📊 Upload"])

with tab1:
    st.markdown("### 📷 Capture Image")
    
    # Camera capture
    camera_image = st.camera_input("Take a picture of the shelf")
    
    if camera_image:
        st.session_state.current_image = camera_image
        st.session_state.analysis_complete = False
        
        # Display captured image in frame
        st.markdown('<div class="camera-frame">', unsafe_allow_html=True)
        st.image(camera_image, caption="Captured Image", use_column_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown("### 📁 Upload Image")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a shelf image...", 
        type=['jpg', 'jpeg', 'png'],
        help="Upload a clear image of store shelves"
    )
    
    if uploaded_file:
        st.session_state.current_image = uploaded_file
        st.session_state.analysis_complete = False
        
        # Display uploaded image
        st.markdown('<div class="camera-frame">', unsafe_allow_html=True)
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# Analysis Configuration & Button
# ---------------------------
if st.session_state.current_image:
    st.markdown("### ⚙️ Analysis Settings")
    
    col1, col2 = st.columns(2)
    with col1:
        expected_count = st.number_input(
            "Expected Products", 
            min_value=1, 
            max_value=100, 
            value=10
        )
    with col2:
        search_text = st.text_input(
            "Brand/Product", 
            value="VI-JOHN"
        )
    
    # Store info
    with st.expander("📍 Store Information (Optional)"):
        store_name = st.text_input("Store Name", value="Reliance Fresh, Indore")
        col3, col4 = st.columns(2)
        with col3:
            analysis_date = st.date_input("Date", value=datetime.now().date())
        with col4:
            analysis_time = st.time_input("Time", value=datetime.now().time())

    # Analysis Button
    if st.button("🔍 Analyze Shelf", type="primary"):
        # Reset previous results
        st.session_state.analysis_complete = False
        st.session_state.analysis_results = None
        st.session_state.output_image_data = None
        
        # Show scanning animation
        with st.container():
            st.markdown('<div class="camera-frame">', unsafe_allow_html=True)
            st.markdown('<p class="scanning-text">📡 Analyzing shelf image...</p>', unsafe_allow_html=True)
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Simulate progress steps
                for i in range(20):
                    progress_bar.progress((i + 1) * 5)
                    status_text.text("🔄 Processing image...")
                    time.sleep(0.05)
                
                # Prepare API call
                files = {"file": (st.session_state.current_image.name, st.session_state.current_image.getvalue(), st.session_state.current_image.type)}
                data = {
                    "expected": expected_count,
                    "search_text": search_text
                }
                
                status_text.text("📡 Sending to server...")
                
                # Make API call
                response = requests.post(
                    ANALYTICS_ENDPOINT,
                    files=files,
                    data=data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    results = response.json()
                    st.session_state.analysis_results = results
                    
                    # Try to fetch processed image
                    try:
                        img_response = requests.get(OUTPUT_IMAGE_ENDPOINT, timeout=30)
                        if img_response.status_code == 200:
                            st.session_state.output_image_data = img_response.content
                    except Exception as img_error:
                        st.warning(f"Could not fetch processed image: {str(img_error)}")
                    
                    st.session_state.analysis_complete = True
                    progress_bar.progress(100)
                    status_text.text("✅ Analysis complete!")
                    time.sleep(1)  # Brief pause to show completion
                    
                else:
                    st.error(f"❌ Analysis failed: {response.status_code}")
                    st.error(f"Response: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to the API server. Please check if it's running.")
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out.")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Request failed: {str(e)}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
            
            st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# Display Results
# ---------------------------
if st.session_state.analysis_complete and st.session_state.analysis_results:
    results = st.session_state.analysis_results
    
    st.markdown("### 📊 Analysis Results")
    
    # Display processed image if available
    if st.session_state.output_image_data:
        try:
            output_image = Image.open(io.BytesIO(st.session_state.output_image_data))
            st.image(output_image, caption="Analysis Results", use_column_width=True)
        except Exception as e:
            st.warning(f"Could not display processed image: {e}")
    
    # Store Information Display
    if 'store_name' in locals() and store_name:
        st.markdown(f"**📍 Store:** {store_name}")
        st.markdown(f"**📅 Date:** {analysis_date.strftime('%d %B %Y')}")
        st.markdown(f"**🕐 Time:** {analysis_time.strftime('%H:%M')}")
    
    # Metrics Summary
    st.markdown("**📊 Metrics Summary:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        osa_value = results.get("OSA", 0)
        st.metric("OSA", f"{osa_value:.1%}")
    with col2:
        sos_value = results.get("SOS", 0)
        st.metric("SoS", f"{sos_value:.1%}")
    with col3:
        total_boxes = results.get("total_boxes", 0)
        st.metric("Total Boxes", total_boxes)
    
    # Status Tag
    osa_value = results.get("OSA", 0)
    if osa_value >= 0.8:
        status = '<span class="status-good">✅ Good Performance</span>'
    elif osa_value >= 0.5:
        status = '<span class="status-moderate">⚠️ Needs Improvement</span>'
    else:
        status = '<span class="status-poor">❌ Needs Attention</span>'
    
    st.markdown(f"**Status:** {status}", unsafe_allow_html=True)
    
    # Detailed Information
    with st.expander("📋 Detailed Information"):
        st.write(f"**Found Products:** {results.get('found', 0)}")
        st.write(f"**Expected Products:** {results.get('expected', 0)}")
        st.write(f"**Search Text:** {search_text}")
        st.write(f"**Total Boxes Detected:** {results.get('total_boxes', 0)}")
        
        # Raw JSON results
        st.json(results)
    
    # Download processed image
    if st.session_state.output_image_data:
        st.download_button(
            label="📥 Download Results",
            data=st.session_state.output_image_data,
            file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
            mime="image/jpeg",
            use_container_width=True
        )

# ---------------------------
# Bottom Navigation (Optional)
# ---------------------------
if not st.session_state.analysis_complete:
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("🏠 **Home**")
    with col2:
        st.markdown("📷 **Capture**")
    with col3:
        st.markdown("📊 **History**")
    with col4:
        st.markdown("👤 **Profile**")

# ---------------------------
# Info Section
# ---------------------------
with st.expander("ℹ️ About Metrics"):
    st.markdown("""
    **OSA (On-Shelf Availability)**
    - Percentage of expected products found on shelf
    
    **SoS (Share of Shelf)**
    - Brand presence among all detected products
    
    **Total Boxes**
    - Total number of product boxes detected on shelf
    """)