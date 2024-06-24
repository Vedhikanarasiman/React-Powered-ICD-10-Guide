from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import tempfile

load_dotenv()

app = FastAPI()

# Allow CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update with your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class QuestionRequest(BaseModel):
    question: str

@app.post("/process-pdf/")
async def process_pdf(files: list[UploadFile]):
    text = ""
    try:
        for file in files:
            print(f"Received file: {file.filename}")
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(await file.read())
                pdf_reader = PdfReader(tmp_file.name)
                for page in pdf_reader.pages:
                    text += page.extract_text()
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")

    text_chunks = get_text_chunks(text)
    get_vector_store(text_chunks)
    return {"message": "PDF processed and vector store created successfully."}

@app.post("/ask-question/")
async def ask_question(request: QuestionRequest):
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        docs = new_db.similarity_search(request.question)

        chain = get_conversation_chain()
        response = chain({"input_documents": docs, "question": request.question}, return_only_outputs=True)
        return {"answer": response["output_text"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embeddings)
    vector_store.save_local("faiss_index")

def get_conversation_chain():
    prompt_template = """
    You are provided with the context from the ICD-10 Volume 3 Alphabetical Index. The context includes terms and their corresponding 
    ICD-10 codes. Your task is to find the most relevant ICD-10 code(s) for the given diagnosis from this context.\n\n
    Context:\n {context}?\n
    Given the diagnosis or condition: \n{question}\n

    Please find and provide the most accurate ICD-10 code(s) that match this diagnosis or condition from the context. If the exact diagnosis is 
    not available, provide the closest possible code(s) related to the diagnosis.

    Answer:
    """
    model = ChatGoogleGenerativeAI(model="gemini-1.0-pro", temperature=0.2)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
