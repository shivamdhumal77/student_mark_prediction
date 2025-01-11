from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import google.generativeai as genai
import easyocr
from typing import Dict
import textwrap

# Configure the Gemini API
genai.configure(api_key="AIzaSyDN0_w4Y91O3njKaBCd-iloOjMFK7S4rV8")

# Initialize FastAPI app
app = FastAPI()

# EasyOCR reader
reader = easyocr.Reader(['en'])

def format_into_paragraphs(text: str, max_width: int = 80) -> str:
    """
    Format a long string into multiple paragraphs for better readability.

    Args:
        text: The input text to format.
        max_width: Maximum width for each line in a paragraph.

    Returns:
        A string with the text divided into paragraphs.
    """
    paragraphs = text.split(". ")  # Split by sentence boundaries
    formatted_paragraphs = "\n\n".join(
        ["\n".join(textwrap.wrap(paragraph.strip(), width=max_width)) for paragraph in paragraphs if paragraph.strip()]
    )
    return formatted_paragraphs

@app.post("/process-image/")
async def process_image(file: UploadFile = File(...)) -> Dict:
    """
    Accepts an image file, extracts text using OCR, and generates responses for summary, improvements, and tips.

    Args:
        file: The uploaded image file.

    Returns:
        A JSON response containing summary, improvements, and tips in formatted paragraphs.
    """
    try:
        # Save uploaded file to a temporary location
        image_path = f"temp_{file.filename}"
        with open(image_path, "wb") as buffer:
            buffer.write(await file.read())

        # Extract text from the image using EasyOCR
        ocr_result = reader.readtext(image_path)
        extracted_text = " ".join([res[1] for res in ocr_result]) if ocr_result else "No text found."

        if extracted_text == "No text found.":
            return JSONResponse(
                {"error": "No text found in the image. Please try again with a different image."},
                status_code=400,
            )

        # Initialize the Gemini model
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Generate summary
        summary_prompt = (
            f"Analyze the following extracted text and provide a detailed summary of each and every subject. Highlight key points, start with the subject and their marks, "
            f"offer insights into the content, and provide an overview of the most relevant details. Ensure the summary is structured, "
            f"easy to understand, and includes actionable information where possible.\n\n{extracted_text}"
        )
        summary_response = model.generate_content(summary_prompt).text
        formatted_summary = format_into_paragraphs(summary_response)

        # Generate improvements
        improvements_prompt = (
            f"Based on the extracted text, identify areas for improvement. Suggest specific, actionable steps to address any weaknesses, "
            f"and provide targeted advice for improving these areas. Include subject-specific strategies or techniques that can be applied, "
            f"and suggest any relevant online resources or links to help with this improvement.\n\n{extracted_text}"
        )
        improvements_response = model.generate_content(improvements_prompt).text
        formatted_improvements = format_into_paragraphs(improvements_response)

        # Generate tips
        tips_prompt = (
            f"Using the extracted text can you predict the future of the student and provide tips for achieving better results?"
            f"seeing the results can you sugggest some career paths for the student and suggest some online courses, books, "
            f"tools, or platforms (including links) that can support better outcomes.\n\n{extracted_text}"
        )
        tips_response = model.generate_content(tips_prompt).text
        formatted_tips = format_into_paragraphs(tips_response)

        # Return all responses in JSON format without including extracted text
        return {
            "summary": formatted_summary,
            "improvements": formatted_improvements,
            "tips": formatted_tips,
        }

    except Exception as e:
        return JSONResponse({"error": f"An error occurred: {str(e)}"}, status_code=500)
