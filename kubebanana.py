import streamlit as st
import google.generativeai as genai
from PIL import Image
from io import BytesIO
from minio import Minio
from minio.error import S3Error
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file as fallback
load_dotenv()

# --- Page config ---
st.set_page_config(page_title="🎨🍌 Gemini 2.5 Multi-Image Editor", layout="wide")

# --- REMOVED ALL CUSTOM CSS ---

# --- Title ---
st.title("🎨🍌 Gemini 2.5 Flash Multi-Image Editor")
st.caption("Transform your images with AI-powered creativity")

# --- Load API Key from environment ---
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("❌ GEMINI_API_KEY environment variable not set.")
    st.stop()

# --- Load S3/MinIO configuration from environment ---
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_SECURE = os.getenv("S3_SECURE", "true").lower() == "true"

s3_configured = all([S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET_NAME])

# Initialize MinIO client if configured
minio_client = None
if s3_configured:
    try:
        minio_client = Minio(
            S3_ENDPOINT,
            access_key=S3_ACCESS_KEY,
            secret_key=S3_SECRET_KEY,
            secure=S3_SECURE
        )
        if not minio_client.bucket_exists(S3_BUCKET_NAME):
            minio_client.make_bucket(S3_BUCKET_NAME)
    except Exception as e:
        st.error(f"❌ MinIO error: {e}")
        minio_client = None

# Configure Gemini
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash-image-preview")
except Exception as e:
    st.error(f"❌ Gemini error: {e}")
    st.stop()

# --- Prompt input ---
st.subheader("📝 Describe Your Vision")
prompt = st.text_area(
    "prompt",
    height=100,
    placeholder="Example: 'Merge these images into an epic cinematic scene with dramatic lighting and intense atmosphere'",
    label_visibility="collapsed"
)

st.divider()

# --- Session state ---
if 'uploaded_images' not in st.session_state:
    st.session_state.uploaded_images = {}
if 'generated_image' not in st.session_state:
    st.session_state.generated_image = None
if 'generated_image_bytes' not in st.session_state:
    st.session_state.generated_image_bytes = None
if 'current_filename' not in st.session_state:
    st.session_state.current_filename = None

st.subheader("📤 Upload Your Images")
st.caption("First image is required • Maximum 4 images • PNG, JPG, JPEG")

# --- Restored 4-Column Layout ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("**Image 1** <span style='color: #dc3545;'>*Required</span>", unsafe_allow_html=True)
    uploaded_image_1 = st.file_uploader("img1", type=["png", "jpg", "jpeg"], key="img1", label_visibility="collapsed")
    if uploaded_image_1:
        img_bytes = uploaded_image_1.read()
        full_img = Image.open(BytesIO(img_bytes))
        st.session_state.uploaded_images['img1'] = full_img
        uploaded_image_1.seek(0)

        # Create thumbnail
        thumb = full_img.copy()
        thumb.thumbnail((200, 200), Image.Resampling.LANCZOS)

        # Native container for thumbnail
        with st.container(border=True):
            st.image(thumb, use_container_width='auto')
            st.success("✓ Ready", icon="✅")
    else:
        st.session_state.uploaded_images.pop('img1', None)  # Clear if removed

with col2:
    st.markdown("**Image 2** <span style='color: #6c757d;'>Optional</span>", unsafe_allow_html=True)
    uploaded_image_2 = st.file_uploader("img2", type=["png", "jpg", "jpeg"], key="img2", label_visibility="collapsed")
    if uploaded_image_2:
        img_bytes = uploaded_image_2.read()
        full_img = Image.open(BytesIO(img_bytes))
        st.session_state.uploaded_images['img2'] = full_img
        uploaded_image_2.seek(0)

        thumb = full_img.copy()
        thumb.thumbnail((200, 200), Image.Resampling.LANCZOS)

        # Native container for thumbnail
        with st.container(border=True):
            st.image(thumb, use_container_width='auto')
            st.success("✓ Ready", icon="✅")
    else:
        st.session_state.uploaded_images.pop('img2', None)  # Clear if removed

with col3:
    st.markdown("**Image 3** <span style='color: #6c757d;'>Optional</span>", unsafe_allow_html=True)
    uploaded_image_3 = st.file_uploader("img3", type=["png", "jpg", "jpeg"], key="img3", label_visibility="collapsed")
    if uploaded_image_3:
        img_bytes = uploaded_image_3.read()
        full_img = Image.open(BytesIO(img_bytes))
        st.session_state.uploaded_images['img3'] = full_img
        uploaded_image_3.seek(0)

        thumb = full_img.copy()
        thumb.thumbnail((200, 200), Image.Resampling.LANCZOS)

        # Native container for thumbnail
        with st.container(border=True):
            st.image(thumb, use_container_width='auto')
            st.success("✓ Ready", icon="✅")
    else:
        st.session_state.uploaded_images.pop('img3', None)  # Clear if removed

with col4:
    st.markdown("**Image 4** <span style='color: #6c757d;'>Optional</span>", unsafe_allow_html=True)
    uploaded_image_4 = st.file_uploader("img4", type=["png", "jpg", "jpeg"], key="img4", label_visibility="collapsed")
    if uploaded_image_4:
        img_bytes = uploaded_image_4.read()
        full_img = Image.open(BytesIO(img_bytes))
        st.session_state.uploaded_images['img4'] = full_img
        uploaded_image_4.seek(0)

        thumb = full_img.copy()
        thumb.thumbnail((200, 200), Image.Resampling.LANCZOS)

        # Native container for thumbnail
        with st.container(border=True):
            st.image(thumb, use_container_width='auto')
            st.success("✓ Ready", icon="✅")
    else:
        st.session_state.uploaded_images.pop('img4', None)  # Clear if removed

st.divider()

# --- Controls ---
col_fmt, col_btn = st.columns([1, 5])

with col_fmt:
    img_format = st.selectbox("Output Format", ["PNG", "JPEG"])

with col_btn:
    # Set button type to "primary" for a native highlight
    generate_btn = st.button("🚀 Generate AI Image", use_container_width=True, type="primary")

# --- Generate ---
if generate_btn:
    # Check against the file uploader object itself, not session state
    if not prompt.strip():
        st.warning("⚠️ Please enter a prompt describing what you want to create")
    elif not uploaded_image_1:
        st.warning("⚠️ Please upload at least the first image")
    else:
        with st.spinner("✨ Creating your masterpiece..."):
            try:
                contents = [prompt.strip()]

                # Use the uploader objects directly as in your original code
                image_files = [uploaded_image_1, uploaded_image_2, uploaded_image_3, uploaded_image_4]
                processed = []

                for idx, img_file in enumerate(image_files, 1):
                    if img_file:
                        img_file.seek(0)
                        # We use the PIL images from session state for consistency
                        pil_img = st.session_state.uploaded_images[f'img{idx}']
                        contents.append(pil_img)
                        processed.append(idx)
                        img_file.seek(0)

                response = model.generate_content(contents, stream=False)

                found_image = False
                text_output = None

                for part in response.parts:
                    if hasattr(part, "text") and part.text:
                        text_output = part.text

                    elif hasattr(part, "inline_data") and part.inline_data:
                        try:
                            img = Image.open(BytesIO(part.inline_data.data))
                            st.session_state.generated_image = img

                            img_bytes = BytesIO()
                            fmt = img_format.upper()
                            img.save(img_bytes, format=fmt)
                            img_bytes.seek(0)
                            st.session_state.generated_image_bytes = img_bytes.getvalue()

                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"gemini_image_{timestamp}.{img_format.lower()}"
                            st.session_state.current_filename = filename

                            if minio_client:
                                try:
                                    img_bytes_copy = BytesIO(st.session_state.generated_image_bytes)

                                    minio_client.put_object(
                                        S3_BUCKET_NAME,
                                        filename,
                                        img_bytes_copy,
                                        length=len(st.session_state.generated_image_bytes),
                                        content_type=f"image/{img_format.lower()}"
                                    )
                                    st.success(f"✅ Image saved to S3: {filename}")
                                except Exception as e:
                                    st.error(f"❌ S3 upload failed: {e}")

                            found_image = True
                        except Exception as img_error:
                            st.error(f"⚠️ Could not load generated image: {img_error}")

                if not found_image:
                    st.error("❌ No image was generated. Please try a different prompt.")
                else:
                    st.success(f"🎉 Successfully generated image using {len(processed)} input image(s)!")

                if text_output:
                    with st.expander("📝 View AI Response Text"):
                        st.write(text_output)

            except Exception as e:
                st.error(f"🚨 An error occurred: {e}")

# --- Results ---
if st.session_state.generated_image:
    st.divider()
    st.subheader("🎨 Your Results")

    num_inputs = len(st.session_state.uploaded_images)
    total_images = num_inputs + 1

    # Ensure at least 1 column, even if 0 inputs (shouldn't happen)
    cols = st.columns(max(total_images, 1))

    col_idx = 0

    # Display input thumbnails
    for key in ['img1', 'img2', 'img3', 'img4']:
        if key in st.session_state.uploaded_images:
            with cols[col_idx]:
                st.markdown(f"**📷 Input {col_idx + 1}**")

                thumb = st.session_state.uploaded_images[key].copy()
                thumb.thumbnail((250, 250), Image.Resampling.LANCZOS)

                # Native container for result thumbnail
                with st.container(border=True):
                    st.image(thumb, use_container_width='auto')
                col_idx += 1

    # Display generated thumbnail
    # Check if col_idx is still valid (it might be out of bounds if no images were processed)
    if col_idx < len(cols):
        with cols[col_idx]:
            st.markdown("**✨ Generated**")

            gen_thumb = st.session_state.generated_image.copy()
            gen_thumb.thumbnail((250, 250), Image.Resampling.LANCZOS)

            # Native container for result thumbnail
            with st.container(border=True):
                st.image(gen_thumb, use_container_width='auto')

    # Download
    st.markdown("") # Adds a bit of space
    col1, col2, col3 = st.columns([2, 2, 2])
    with col2:
        st.download_button(
            "⬇️ Download Generated Image",
            data=st.session_state.generated_image_bytes,
            file_name=st.session_state.current_filename,
            mime=f"image/{img_format.lower()}",
            use_container_width=True
        )

# --- Tips ---
st.divider()
with st.expander("💡 Tips for Amazing Results"):
    st.markdown("""
    **Prompt Writing Tips:**
    - Be specific and detailed about what you want
    - Mention artistic style, mood, lighting, and atmosphere
    - Describe the composition and perspective
    
    **Example Prompts:**
    - *"Transform me into a cowboy riding a horse through a misty forest at sunset, cinematic lighting, dramatic close-up on face"*
    - *"Combine these images into a futuristic cyberpunk cityscape with neon lights and rain"*
    - *"Create an artistic collage with watercolor effect and soft pastel colors"*
    - *"Merge these portraits into a movie poster style with epic dramatic lighting"*
    """)

with st.expander("🔧 Configuration & Setup"):
    st.markdown("""
    **Required Environment Variables:**
    - `GEMINI_API_KEY` - Your Google Gemini API key
    
    **Optional (for S3/MinIO storage):**
    - `S3_ENDPOINT` - e.g., "localhost:9000"
    - `S3_ACCESS_KEY` - Access key
    - `S3_SECRET_KEY` - Secret key
    - `S3_BUCKET_NAME` - Bucket name
    - `S3_SECURE` - "true" or "false"
    
    Set these in your environment or create a `.env` file in the same directory.
    """)

    if s3_configured:
        st.success("✅ S3/MinIO storage is configured and active")
    else:
        st.info("ℹ️ S3/MinIO storage not configured - images available for download only")
