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
st.set_page_config(page_title="🎨🍌 Gemini 2.5 Multi-Image Editor", layout="centered")

# Centered title using HTML
st.markdown(
    "<h2 style='text-align: center;'>🎨🍌 Gemini 2.5 Flash Multi-Image Editor</h2>",
    unsafe_allow_html=True
)

# --- Load API Key from environment ---
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("❌ GEMINI_API_KEY environment variable not set. Please configure it in your environment or .env file and restart the app.")
    st.stop()

# --- Load S3/MinIO configuration from environment ---
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_SECURE = os.getenv("S3_SECURE", "true").lower() == "true"  # Default to True

# Validate S3 configuration
s3_configured = all([S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET_NAME])

if not s3_configured:
    st.warning("⚠️ S3/MinIO configuration incomplete. Image saving to object storage will be disabled.")
    st.info("Required environment variables: S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET_NAME, S3_SECURE (optional)")

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
        # Check if bucket exists, create if not
        if not minio_client.bucket_exists(S3_BUCKET_NAME):
            minio_client.make_bucket(S3_BUCKET_NAME)
            st.success(f"✅ Created bucket: {S3_BUCKET_NAME}")
    except Exception as e:
        st.error(f"❌ Failed to initialize MinIO client: {e}")
        minio_client = None

# Configure Gemini
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash-image-preview")
except Exception as e:
    st.error(f"❌ Invalid API key or model error: {e}")
    st.stop()

# --- Prompt input ---
prompt = st.text_area("📝 Enter your image prompt (e.g. 'Merge these images into a cinematic scene')", height=150)

# --- Image uploaders (4 separate boxes, first is mandatory) ---
st.markdown("### 📤 Upload Images")
st.markdown("*First image is mandatory, others are optional*")

col1, col2 = st.columns(2)

with col1:
    uploaded_image_1 = st.file_uploader(
        "📷 Image 1 (Required)",
        type=["png", "jpg", "jpeg"],
        key="img1"
    )
    
with col2:
    uploaded_image_2 = st.file_uploader(
        "📷 Image 2 (Optional)",
        type=["png", "jpg", "jpeg"],
        key="img2"
    )

col3, col4 = st.columns(2)

with col3:
    uploaded_image_3 = st.file_uploader(
        "📷 Image 3 (Optional)",
        type=["png", "jpg", "jpeg"],
        key="img3"
    )
    
with col4:
    uploaded_image_4 = st.file_uploader(
        "📷 Image 4 (Optional)",
        type=["png", "jpg", "jpeg"],
        key="img4"
    )

# --- Format selector ---
img_format = st.selectbox("🖼️ Choose Download Format", ["PNG", "JPEG"])

# --- Generate button ---
if st.button("🚀 Generate"):
    if not prompt.strip():
        st.warning("⚠️ Please enter a prompt.")
    elif not uploaded_image_1:
        st.warning("⚠️ You must upload at least the first image.")
    else:
        with st.spinner("✨ Generating image..."):
            try:
                contents = [prompt.strip()]
                
                # Collect all uploaded images
                uploaded_images = []
                for idx, img_file in enumerate([uploaded_image_1, uploaded_image_2, uploaded_image_3, uploaded_image_4], 1):
                    if img_file:
                        try:
                            image_bytes = img_file.read()
                            pil_img = Image.open(BytesIO(image_bytes))
                            st.image(pil_img, caption=f"📷 Uploaded Image {idx}: {img_file.name}", use_container_width=True)
                            contents.append(pil_img)
                            uploaded_images.append(img_file.name)
                        except Exception as e:
                            st.warning(f"⚠️ Could not read image {img_file.name}: {e}")
                            st.stop()

                st.info(f"📊 Processing {len(uploaded_images)} image(s)...")

                # Generate using Gemini
                response = model.generate_content(contents, stream=False)

                # Parse result
                found_image = False
                for part in response.parts:
                    if hasattr(part, "text") and part.text:
                        st.markdown("### 📝 Text Output")
                        st.write(part.text)

                    elif hasattr(part, "inline_data") and part.inline_data:
                        try:
                            img = Image.open(BytesIO(part.inline_data.data))
                            st.image(img, caption="🖼️ Generated Image", use_container_width=True)

                            # Prepare for download
                            img_bytes = BytesIO()
                            fmt = img_format.upper()
                            img.save(img_bytes, format=fmt)
                            img_bytes.seek(0)

                            # Generate filename with timestamp
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"gemini_image_{timestamp}.{img_format.lower()}"

                            # Save to S3/MinIO if configured
                            if minio_client:
                                try:
                                    img_bytes_copy = BytesIO()
                                    img.save(img_bytes_copy, format=fmt)
                                    img_bytes_copy.seek(0)
                                    
                                    minio_client.put_object(
                                        S3_BUCKET_NAME,
                                        filename,
                                        img_bytes_copy,
                                        length=img_bytes_copy.getbuffer().nbytes,
                                        content_type=f"image/{img_format.lower()}"
                                    )
                                    st.success(f"✅ Image saved to S3: {S3_BUCKET_NAME}/{filename}")
                                except S3Error as s3_err:
                                    st.error(f"❌ Failed to upload to S3: {s3_err}")
                                except Exception as upload_err:
                                    st.error(f"❌ Upload error: {upload_err}")

                            # Download button
                            st.download_button(
                                label="⬇️ Download Image",
                                data=img_bytes,
                                file_name=filename,
                                mime=f"image/{img_format.lower()}",
                            )
                            found_image = True
                        except Exception as img_error:
                            st.warning(f"⚠️ Could not load generated image: {img_error}")

                if not found_image:
                    st.error("❌ No image output found. Try another prompt or different images.")

            except Exception as e:
                st.error(f"🚨 An error occurred: {e}")

# --- Prompt Tips ---
st.markdown("---")
st.markdown("""
### 💡 Prompt Writing Tips

- 🧠 Describe your intent clearly
- 🎨 Specify style, tone, or purpose
- 🖼️ Useful examples:
  - "Give me long blond hair, slicked back. Put me like a cowboy riding a horse, hunting thieves through the forest with energy and intensity. Close up on my face."
  - "Create a before-and-after restoration"
  - "Combine these into a futuristic landscape"
  - "Turn these faces into a single stylized portrait"
  - "Merge all images into a cohesive collage"
""")

st.markdown("---")
st.markdown("""
### 🔧 Environment Variables Required

**Gemini API:**
- `GEMINI_API_KEY` - Your Google Gemini API key

**S3/MinIO Storage (Optional):**
- `S3_ENDPOINT` - MinIO/S3 endpoint (e.g., "localhost:9000" or "s3.amazonaws.com")
- `S3_ACCESS_KEY` - Access key
- `S3_SECRET_KEY` - Secret key
- `S3_BUCKET_NAME` - Bucket name to store images
- `S3_SECURE` - Use HTTPS (true/false, default: true)

**Configuration Options:**
1. Set as system environment variables, OR
2. Create a `.env` file in the same directory as this script
""")
