import streamlit as st
import requests
from PIL import Image
import io
import base64
import os
from dotenv import load_dotenv

# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()

# Page config
st.set_page_config(
    page_title="Shelf Analytics Dashboard",
    page_icon="📊",
    layout="centered"
)

# Title and header
st.title("📊 Shelf Analytics Dashboard")
st.markdown("Upload shelf images to analyze OSA, SOS metrics and detect product boxes")

# API endpoint configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
ANALYTICS_ENDPOINT = f"{API_BASE_URL}/api/analytics/analyze"

# Sidebar for configuration (overrides .env)
st.sidebar.header("Configuration")
api_url = st.sidebar.text_input(
    "API URL", 
    value=API_BASE_URL, 
    help="Enter your FastAPI server URL"
)
ANALYTICS_ENDPOINT = f"{api_url}/api/analytics/analyze"

# ---------------------------
# Main interface
# ---------------------------
st.header("Upload Image for Analysis")

# File upload
uploaded_file = st.file_uploader(
    "Choose a shelf image...", 
    type=['jpg', 'jpeg', 'png'],
    help="Upload a clear image of store shelves for analysis"
)

# Expected count input
expected_count = st.number_input(
    "Expected Number of Target Products", 
    min_value=1, 
    max_value=100, 
    value=10,
    help="Enter the expected number of products on the shelf"
)

# ---------------------------
# Analyze button
# ---------------------------
if st.button("🔍 Analyze Image", type="primary"):
    if uploaded_file is not None:
        # Show uploaded image
        image = Image.open(uploaded_file)
        st.subheader("📸 Original Image")
        st.image(image, caption="Uploaded Image", use_column_width=True)
        
        # Show loading spinner
        with st.spinner("Analyzing image... This may take a few seconds."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                data = {"expected": expected_count}
                
                response = requests.post(
                    ANALYTICS_ENDPOINT,
                    files=files,
                    data=data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    results = response.json()
                    st.success("✅ Analysis completed successfully!")
                    
                    # ---------------------------
                    # Display processed image
                    # ---------------------------
                    if 'output_image' in results:
                        st.subheader("🔍 Analysis Results Image")
                        try:
                            output_image_data = base64.b64decode(results['output_image'])
                            output_image = Image.open(io.BytesIO(output_image_data))
                            st.image(output_image, caption="Processed Image with Detections", use_column_width=True)
                        except Exception as img_error:
                            st.warning(f"⚠️ Could not display processed image: {str(img_error)}")
                    
                    elif 'output_image_url' in results:
                        st.subheader("🔍 Analysis Results Image")
                        st.image(results['output_image_url'], caption="Processed Image with Detections", use_column_width=True)
                    
                    elif os.path.exists("output.jpg"):
                        st.subheader("🔍 Analysis Results Image")
                        output_image = Image.open("output.jpg")
                        st.image(output_image, caption="Processed Image with Detections", use_column_width=True)
                    else:
                        st.info("ℹ️ No processed image found.")
                    
                    # ---------------------------
                    # Metrics
                    # ---------------------------
                    st.subheader("📊 Analysis Metrics")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("OSA (On-Shelf Availability)", f"{results['OSA']:.1%}")
                    with col2:
                        st.metric("SOS (Share of Shelf)", f"{results['SOS']:.1%}")
                    with col3:
                        st.metric("Total Boxes Detected", results['total_boxes'])
                    
                    # ---------------------------
                    # Detailed Results
                    # ---------------------------
                    st.subheader("📋 Detailed Results")
                    col4, col5 = st.columns(2)
                    
                    with col4:
                        st.info(f"**Found Products:** {results['found']}")
                        st.info(f"**Expected Products:** {results['expected']}")
                    
                    with col5:
                        if results['OSA'] >= 0.8:
                            availability_status = "🟢 Good Availability"
                        elif results['OSA'] >= 0.5:
                            availability_status = "🟡 Moderate Availability"
                        else:
                            availability_status = "🔴 Low Availability"
                        
                        st.markdown(f"**Availability Status:** {availability_status}")
                        
                        if results['SOS'] >= 0.3:
                            shelf_status = "🟢 Good Shelf Presence"
                        elif results['SOS'] >= 0.15:
                            shelf_status = "🟡 Moderate Shelf Presence"
                        else:
                            shelf_status = "🔴 Low Shelf Presence"
                        
                        st.markdown(f"**Shelf Presence:** {shelf_status}")
                    
                    # ---------------------------
                    # Download Processed Image
                    # ---------------------------
                    if 'output_image' in results:
                        st.subheader("💾 Download Processed Image")
                        output_image_data = base64.b64decode(results['output_image'])
                        st.download_button(
                            label="📥 Download Analysis Results Image",
                            data=output_image_data,
                            file_name="analysis_output.jpg",
                            mime="image/jpeg"
                        )
                    elif os.path.exists("output.jpg"):
                        st.subheader("💾 Download Processed Image")
                        with open("output.jpg", "rb") as file:
                            st.download_button(
                                label="📥 Download Analysis Results Image",
                                data=file.read(),
                                file_name="analysis_output.jpg",
                                mime="image/jpeg"
                            )
                    
                    # Raw JSON results
                    with st.expander("🔍 View Raw Results"):
                        st.json(results)
                        
                else:
                    st.error(f"❌ API Error: {response.status_code}")
                    st.error(f"Response: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to the API server. Please check if it's running.")
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out.")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Request failed: {str(e)}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
    else:
        st.warning("⚠️ Please upload an image first.")

# ---------------------------
# Info Section
# ---------------------------
st.markdown("---")
st.subheader("ℹ️ About the Metrics")

col_info1, col_info2 = st.columns(2)
with col_info1:
    st.markdown("""
    **OSA (On-Shelf Availability)**
    - Measures if products are available on shelf  
    - Formula: Found Products / Expected Products  
    - Higher is better (100% = all expected products found)
    """)
with col_info2:
    st.markdown("""
    **SOS (Share of Shelf)**
    - Measures brand presence among all products  
    - Formula: Target Products / Total Detected Boxes  
    - Shows competitive positioning
    """)

# ---------------------------
# Footer
# ---------------------------
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <small>Shelf Analytics Dashboard | Powered by YOLO + OCR</small>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------------
# Custom CSS
# ---------------------------
st.markdown("""
<style>
.metric-container {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}
.stButton > button {
    width: 100%;
    margin-top: 1rem;
}
.uploadedFile {
    border: 2px dashed #ccc;
    border-radius: 10px;
    padding: 20px;
    text-align: center;
}
.stImage > div {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 10px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)
