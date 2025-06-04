# This is a simple Streamlit app for the Radiology Prediction UI.
# It allows users to upload frontal and lateral images, enter indications,
# Run the Streamlit app
# To run the app, use the command: streamlit run index.py

import streamlit as st
import requests
import uuid

def main():
    st.set_page_config(page_title="ARGS", layout="wide")

    # Apply CSS for consistent image and layout
    st.markdown("""
        <style>
        .uploadedImage {
            max-height: 300px;
            object-fit: contain;
        }
        .reportBox {
            max-height: 400px;
            overflow-y: auto;
        }
        .stTextArea textarea {
            min-height: 100px;
        }
        .studyBox {
            background-color: #f5f5f5;
            border-radius: 10px;
            padding: 10px;
            margin-bottom: 10px;
        }
        .studyTitle {
            font-weight: bold;
            font-size: 16px;
            color: #2c3e50;
        }
        .studyAuthors {
            font-size: 14px;
            color: #7f8c8d;
        }
        .studyAbstract {
            font-size: 13px;
            color: #34495e;
        }
        a {
            color: #2980b9;
            text-decoration: none;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("Automated Radiology Report Generation and Suggestion (ARGS)")

    uid = str(uuid.uuid4())
    st.caption(f"Generated UID: `{uid}`")

    # Indications text box at the top
    indications = st.text_area("Indications", help="Provide relevant indications here.")

    # Numeric input for maxStudies
    max_studies = st.number_input(
        "Maximum Number of Relevant Studies to Fetch",
        min_value=1,
        max_value=20,
        value=5,
        step=1,
        help="Specify the maximum number of relevant studies to fetch (default is 5)."
    )

    # Arrange image uploaders side by side
    col1, col2 = st.columns(2)
    with col1:
        frontal_image = st.file_uploader("Upload Frontal Image", type=["jpg", "jpeg", "png"])
    with col2:
        lateral_image = st.file_uploader("Upload Lateral Image", type=["jpg", "jpeg", "png"])

    # Show uploaded images with consistent size
    col3, col4 = st.columns(2)
    with col3:
        if frontal_image:
            st.image(frontal_image, caption="Frontal Image", use_container_width=True, output_format="JPEG")
    with col4:
        if lateral_image:
            st.image(lateral_image, caption="Lateral Image", use_container_width=True, output_format="JPEG")

    st.markdown("---")

    if st.button("Submit"):
        if not (frontal_image and lateral_image and indications.strip()):
            st.error("Please upload both images and provide indications.")
        else:
            # Reset file pointers
            frontal_image.seek(0)
            lateral_image.seek(0)

            files = {
                "uid": (None, uid),
                "frontalImage": (frontal_image.name, frontal_image, frontal_image.type),
                "lateralImage": (lateral_image.name, lateral_image, lateral_image.type),
                "indications": (None, indications),
                "maxStudies": (None, str(max_studies))
            }

            try:
                response = requests.post(
                    "http://127.0.0.1:8000/get-prediction",
                    files=files,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                st.success("Prediction received!")

                for item in data:
                    st.markdown(f"### UID: `{item['uid']}`")
                    st.markdown(f"**Findings:** {item['findings']}")
                    st.markdown(f"**Impression:** {item['impression']}")
                    
                    if "medical_studies" in item and item["medical_studies"]:
                        with st.expander("📚 Relevant Studies"):
                            for study in item["medical_studies"]:
                                st.markdown(f"""
                                    <div class="studyBox">
                                        <div class="studyTitle">{study['title']}</div>
                                        <div class="studyAuthors">{"; ".join(study['authors'])}</div>
                                        <div class="studyAbstract">{study['abstract'][:500]}{"..." if len(study['abstract']) > 500 else ""}</div>
                                        <a href="{study['link']}" target="_blank">Read more</a>
                                    </div>
                                """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
