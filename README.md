# 🎨🍌 KubeBanana: Gemini 2.5 Multi-Image Editor

KubeBanana is a powerful and intuitive web application built with Streamlit that allows you to harness the creative potential of Google's Gemini 2.5 Flash model. Upload multiple images, provide a descriptive prompt, and watch as the AI transforms them into a single, stunning masterpiece.

## ✨ Features

- **Multi-Image Input:** Combine up to four images to create unique compositions.
- **AI-Powered Image Generation:** Utilizes the cutting-edge Gemini 2.5 Flash model for high-quality results.
- **Intuitive Web Interface:** A user-friendly Streamlit interface makes image editing a breeze.
- **Flexible Storage Options:** Save images to your local filesystem, an S3/MinIO bucket, or just download them directly.
- **Customizable Options:** Adjust thumbnail sizes and choose to organize saved images by date.
- **Prompting Guidance:** Get tips and examples for writing effective prompts to achieve your desired results.

## 🚀 Prerequisites

Before you begin, ensure you have the following:

- Python 3.7+
- A Google Gemini API key.

## 🛠️ Installation & Usage

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/kubebanana.git
    cd kubebanana
    ```

2.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up your environment variables:**

    Create a `.env` file in the root of the project and add your Gemini API key:
    ```
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    ```

4.  **Run the Streamlit application:**
    ```bash
    streamlit run kubebanana.py
    ```

    The application will be accessible at `http://localhost:8501`.

## ⚙️ Configuration

KubeBanana uses environment variables for configuration. The application has three save modes with the following priority: Filesystem > S3 > Memory.

### Required

-   `GEMINI_API_KEY`: Your Google Gemini API key.

### Optional (for Filesystem Storage)

-   `FILESYSTEM_SAVE_PATH`: The absolute path to a directory on your local filesystem where you want to save the generated images.

### Optional (for S3/MinIO Storage)

-   `S3_ENDPOINT`: The endpoint of your S3-compatible storage (e.g., "localhost:9000").
-   `S3_ACCESS_KEY`: Your access key.
-   `S3_SECRET_KEY`: Your secret key.
-   `S3_BUCKET_NAME`: The name of the bucket to store your images.
-   `S3_SECURE`: Set to "true" for HTTPS, "false" for HTTP.

## 📄 License

This project is licensed under the terms of the LICENSE file.