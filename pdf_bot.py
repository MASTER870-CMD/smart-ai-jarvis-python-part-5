import PyPDF2
import os

def extract_text_from_pdf(pdf_path):
    """
    Reads a PDF file and returns the text.
    Limits to first 10 pages to avoid overloading the AI.
    """
    try:
        if not os.path.exists(pdf_path):
            return None
        
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            # Read up to 10 pages or the max pages in the file
            num_pages = len(reader.pages)
            limit = min(10, num_pages)
            
            for i in range(limit):
                page = reader.pages[i]
                if page.extract_text():
                    text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def get_pdf_summary(filename, file_path, client, model_id):
    """
    Sends PDF text to Groq AI for a summary.
    """
    # 1. Extract Text
    raw_text = extract_text_from_pdf(file_path)
    
    if not raw_text:
        return "I could not read the PDF text. It might be an image-only PDF."

    # 2. Send to AI
    try:
        sys_prompt = "You are an expert analyst. Summarize the document into 5 distinct bullet points. Do NOT use asterisks (*), bolding, or markdown. Just use plain text with dashes (-)."
        
        # Truncate text to fit context window
        safe_text = raw_text[:15000]
        
        completion = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": f"Summarize this text from {filename}:\n\n{safe_text}"}
            ]
        )
        
        # 3. Clean the Output (Remove * and # just in case)
        clean_response = completion.choices[0].message.content
        clean_response = clean_response.replace("*", "").replace("#", "").strip()
        
        return clean_response
        
    except Exception as e:
        return f"AI Summarization failed: {str(e)}"