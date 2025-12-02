import streamlit as st
import google.generativeai as genai
from PIL import Image
from io import BytesIO
from minio import Minio
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Page setup ---
st.set_page_config(page_title="🎨🍌 Gemini nano-banana Multi-Image Editor", layout="wide")
st.title("🎨🍌 Gemini nano-banana Multi-Image Editor")
st.caption("Transform your images with AI-powered creativity")

# --- API key ---
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("❌ GEMINI_API_KEY environment variable not set.")
    st.stop()

# --- S3 / MinIO configuration ---
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_SECURE = os.getenv("S3_SECURE", "true").lower() == "true"

s3_configured = all([S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET_NAME])
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
        st.error(f"❌ MinIO init error: {e}")
        minio_client = None
        s3_configured = False

# --- Filesystem save configuration ---
FILESYSTEM_SAVE_PATH = os.getenv("FILESYSTEM_SAVE_PATH")
filesystem_configured = bool(FILESYSTEM_SAVE_PATH and os.path.isdir(FILESYSTEM_SAVE_PATH))

# Determine save mode: priority FS > S3 > memory
if filesystem_configured:
    save_mode = "filesystem"
elif s3_configured:
    save_mode = "s3"
else:
    save_mode = "memory"

# --- Gemini configuration ---
try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"❌ Gemini setup error: {e}")
    st.stop()

# --- Sidebar configuration display and options ---
st.sidebar.header("⚙️ Configuration & Options")

st.sidebar.subheader("Save Mode")
st.sidebar.write(f"Mode: **{save_mode.upper()}**")
if save_mode == "filesystem":
    st.sidebar.write(f"Directory: {FILESYSTEM_SAVE_PATH}")
elif save_mode == "s3":
    st.sidebar.write(f"Bucket: {S3_BUCKET_NAME}")
    st.sidebar.write(f"Endpoint: {S3_ENDPOINT}")
    st.sidebar.write(f"Secure: {S3_SECURE}")
else:
    st.sidebar.info("Images will only be available for download (not stored persistently)")

st.sidebar.subheader("Model")
model_choice = st.sidebar.selectbox(
    "Select Model",
    ["gemini-3.0-nano-banana-pro", "gemini-2.5-flash-image-preview"],
    index=0
)

if model_choice == "gemini-3.0-nano-banana-pro":
    image_ratio = st.sidebar.selectbox(
        "Image Ratio",
        ["1:1", "16:9", "4:3", "3:4", "9:16"],
        index=0
    )

thumb_size = st.sidebar.slider("Thumbnail size (pixels)", min_value=100, max_value=600, value=300, step=50)
save_with_date_folder = st.sidebar.checkbox("Save under date-named folder (YYYY-MM-DD)", value=False)

st.sidebar.markdown("---")

# --- Model Instantiation ---
model_mapping = {
    "gemini-2.5-flash-image-preview": "gemini-2.5-flash-image-preview",
    "gemini-3.0-nano-banana-pro": "gemini-3-pro-image-preview"
}

try:
    api_model_name = model_mapping[model_choice]
    model = genai.GenerativeModel(api_model_name)
except Exception as e:
    st.error(f"❌ Model initialization error: {e}")
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

# --- Session state initialization ---
if 'uploaded_images' not in st.session_state:
    st.session_state.uploaded_images = {}
if 'generated_image' not in st.session_state:
    st.session_state.generated_image = None
if 'generated_image_bytes' not in st.session_state:
    st.session_state.generated_image_bytes = None
if 'current_filename' not in st.session_state:
    st.session_state.current_filename = None

# --- Image upload UI ---
st.subheader("📤 Upload Your Images")
st.caption("First image is required • Maximum 4 images • PNG, JPG, JPEG")

cols = st.columns(4)
for i, col in enumerate(cols, start=1):
    with col:
        label = f"Image {i}" + (" *Required" if i == 1 else " (Optional)")
        st.markdown(f"**{label}**", unsafe_allow_html=True)
        uploader = st.file_uploader(f"img{i}", type=["png", "jpg", "jpeg"], key=f"img{i}", label_visibility="collapsed")
        if uploader:
            img_bytes = uploader.read()
            img = Image.open(BytesIO(img_bytes)).convert("RGB")
            st.session_state.uploaded_images[f'img{i}'] = img
            uploader.seek(0)
            thumb = img.copy()
            thumb.thumbnail((thumb_size, thumb_size), Image.Resampling.LANCZOS)
            with st.container():
                st.image(thumb)
                st.success("✓ Ready", icon="🎉")
        else:
            st.session_state.uploaded_images.pop(f'img{i}', None)

st.divider()

# --- Generate button ---
generate_btn = st.button("🚀 Generate AI Image", use_container_width=True)

if generate_btn:
    if not prompt.strip():
        st.warning("⚠️ Please enter a prompt describing what you want to create")
    elif 'img1' not in st.session_state.uploaded_images:
        st.warning("⚠️ Please upload at least the first image")
    else:
        with st.spinner("✨ Creating your masterpiece..."):
            try:
                # Incorporate model-specific settings into the prompt
                final_prompt = prompt.strip()
                if model_choice == "gemini-3.0-nano-banana-pro":
                    final_prompt += f"\n\nSpecifications:\n- Aspect Ratio: {image_ratio}"
                
                contents = [final_prompt]
                processed = []
                for i in range(1,5):
                    key = f'img{i}'
                    if key in st.session_state.uploaded_images:
                        contents.append(st.session_state.uploaded_images[key])
                        processed.append(key)
                
                response = model.generate_content(
                    contents, 
                    stream=False
                )

                found_image = False
                text_output = None

                for part in response.parts:
                    if hasattr(part, "text") and part.text:
                        text_output = part.text
                    elif hasattr(part, "inline_data") and part.inline_data:
                        img = Image.open(BytesIO(part.inline_data.data)).convert("RGB")
                        st.session_state.generated_image = img

                        # Always save as PNG
                        img_bytes = BytesIO()
                        img.save(img_bytes, format="PNG")
                        img_bytes.seek(0)
                        st.session_state.generated_image_bytes = img_bytes.getvalue()

                        # Build filename
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        base_name = f"gemini_image_{timestamp}.png"

                        # Apply date folder if requested
                        if save_with_date_folder:
                            date_str = datetime.now().strftime("%Y-%m-%d")
                            base_name = os.path.join(date_str, base_name)

                        st.session_state.current_filename = base_name

                        # Save according to mode
                        if save_mode == "filesystem":
                            full_path = os.path.join(FILESYSTEM_SAVE_PATH, base_name)
                            # Ensure directory exists
                            dir_path = os.path.dirname(full_path)
                            os.makedirs(dir_path, exist_ok=True)
                            with open(full_path, "wb") as f:
                                f.write(st.session_state.generated_image_bytes)
                            st.success(f"✅ Saved to filesystem: {full_path}")

                        elif save_mode == "s3" and minio_client:
                            try:
                                minio_client.put_object(
                                    S3_BUCKET_NAME,
                                    base_name.replace("\\", "/"),
                                    BytesIO(st.session_state.generated_image_bytes),
                                    length=len(st.session_state.generated_image_bytes),
                                    content_type="image/png"
                                )
                                st.success(f"✅ Saved to S3: {base_name}")
                            except Exception as e:
                                st.error(f"❌ S3 upload failed: {e}")

                        else:
                            # Memory-only
                            st.info("ℹ️ Image is available for download only (not stored permanently)")

                        found_image = True

                if not found_image:
                    st.error("❌ No image was generated. Please try a different prompt.")
                else:
                    st.success(f"🎉 Successfully generated image using {len(processed)} input image(s)!")

                if text_output:
                    with st.expander("📝 View AI Response Text"):
                        st.write(text_output)

            except Exception as e:
                st.error(f"🚨 An error occurred: {e}")

# --- Results display ---
if st.session_state.generated_image:
    st.divider()
    st.subheader("🎨 Your Results")

    num_inputs = len(st.session_state.uploaded_images)
    cols_out = st.columns(num_inputs + 1)
    col_idx = 0

    for key in ['img1','img2','img3','img4']:
        if key in st.session_state.uploaded_images:
            with cols_out[col_idx]:
                st.markdown(f"**📷 Input {col_idx+1}**")
                thumb = st.session_state.uploaded_images[key].copy()
                thumb.thumbnail((thumb_size, thumb_size), Image.Resampling.LANCZOS)
                st.image(thumb)
                if st.button(f"🔍 View full Input {col_idx}", key=f"view_full_input_{key}"):
                    st.image(st.session_state.uploaded_images[key])
                col_idx += 1

    with cols_out[col_idx]:
        st.markdown("**✨ Generated**")
        gen_thumb = st.session_state.generated_image.copy()
        gen_thumb.thumbnail((thumb_size, thumb_size), Image.Resampling.LANCZOS)
        st.image(gen_thumb)
        if st.button("🔍 View full Generated", key="view_full_generated"):
            st.image(st.session_state.generated_image)

    st.markdown("<br>", unsafe_allow_html=True)
    dl_cols = st.columns([2,2,2])
    with dl_cols[1]:
        st.download_button(
            "⬇️ Download Generated Image",
            data=st.session_state.generated_image_bytes,
            file_name=os.path.basename(st.session_state.current_filename),
            mime="image/png",
            use_container_width=True
        )

# --- Updated Inspiration & Example Prompts Section (English README, fixed rendering) ---
st.divider()
with st.expander("💡 Inspiration & Example Prompts (from Awesome-Nano-Banana-Images)"):
    st.markdown("""
    Want to generate amazing images with this same model (Nano-Banana / Gemini-2.5-flash-image)?  
    Check out the [Awesome-Nano-Banana-Images Gallery (English)](https://github.com/PicoTrex/Awesome-Nano-Banana-images/blob/main/README_en.md) for prompts + outputs curated to inspire creativity.

    Here are some example prompts drawn from that collection:

    - `Turn illustrations into figures` — upload an illustration and convert it to a 3D figure or toy-like model  
    - `Photos of yourself from different eras` — take a portrait and generate versions in styles from various historical periods  
    - `Coloring the line art using a color palette` — upload line art and a color palette reference and color accordingly  
    - `Change into a specific outfit` — specify desired clothing and style details for the subject in the image  

    """)


    st.markdown("🔗 Explore all the examples & prompts → [Awesome-Nano-Banana-Images (English)](https://github.com/PicoTrex/Awesome-Nano-Banana-images/blob/main/README_en.md)")

with st.expander("🔧 Configuration & Setup"):
    st.markdown("""
    **Required Environment Variables:**
    - `GEMINI_API_KEY` — your Google Gemini API key

    **Optional Environment Variables (for saving outputs):**
    - `FILESYSTEM_SAVE_PATH` — path to a directory on the local filesystem  
    - `S3_ENDPOINT` — e.g., `"localhost:9000"`  
    - `S3_ACCESS_KEY` — your MinIO/S3 access key  
    - `S3_SECRET_KEY` — your MinIO/S3 secret key  
    - `S3_BUCKET_NAME` — bucket name to store images  
    - `S3_SECURE` — `"true"` or `"false"` to indicate SSL TLS usage for S3  

    **Options You Can Adjust in the Sidebar:**
    - Thumbnail size (for previews)  
    - Whether to save images under a date-based subdirectory (YYYY-MM-DD)  
    - Save mode is auto-selected (Filesystem > S3 > memory) depending on which configs are set  

    **Behavior Summary:**
    - If `FILESYSTEM_SAVE_PATH` is set and valid → images are saved to the filesystem  
    - Else if S3 credentials are valid → saved to S3 / MinIO  
    - Otherwise → image is kept in memory and only available for download  

    Make sure to set these variables in your environment or a `.env` file in the same directory.
    """)

# Optional feedback on storage status
if save_mode == "filesystem":
    st.sidebar.success("✅ Filesystem saving is active")
elif save_mode == "s3":
    st.sidebar.success("✅ S3/MinIO saving is active")
else:
    st.sidebar.info("ℹ️ No persistent storage configured; images can only be downloaded")
