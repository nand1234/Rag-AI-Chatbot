from langchain_community.document_loaders import WebBaseLoader, PDFMinerLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document  # Adjust import based on your library
import tempfile
import io, os



DB_dir: str = f"./langchain/"

def load_documents(url: str = "https://lilianweng.github.io/posts/2023-06-23-agent/"):
    loader = WebBaseLoader(url)
    data = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=500)
    all_splits = text_splitter.split_documents(data)

    local_embidding = HuggingFaceEmbeddings()

    Chroma.from_documents(documents=all_splits, embedding=local_embidding, persist_directory=DB_dir)
    
def document_exists(new_documents, vectorstore):
    for doc in new_documents:
        # Perform similarity search for each split
        results = vectorstore.similarity_search(doc.page_content, k=1)
        if results and results[0].page_content == doc.page_content:
            return True  # Document already exists
    return False


def load_pdf(pdf, pdf_name):
    
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(pdf.read())
        temp_file_path = temp_file.name  # Get the temporary file path
    loader = PDFMinerLoader(temp_file_path)
    data = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=500)
    all_splits = text_splitter.split_documents(data)

    # Add metadata (PDF name) to each document chunk
    for split in all_splits:
        split.metadata['source'] = os.path.basename(pdf_name)


    local_embidding = HuggingFaceEmbeddings()

    vectorstore = Chroma(persist_directory=DB_dir, embedding_function=local_embidding)

    # Check for duplicates before inserting
    if not document_exists(all_splits, vectorstore):
        Chroma.from_documents(documents=all_splits, embedding=local_embidding, persist_directory=DB_dir)
        return(f"Successfully added {pdf_name} to the vector store.")
    else:
        return(f"{pdf_name} already exists in the vector store. Skipping insertion.")
        
def get_context(question, pdf_name):
    local_embidding = HuggingFaceEmbeddings()
    vectorstore = Chroma(persist_directory=DB_dir, embedding_function=local_embidding)
    docs = vectorstore.similarity_search(question, k=3)
    #print(docs)
    filtered_docs = [doc for doc in docs if doc.metadata.get('source') == os.path.basename(pdf_name)]
    combined_page_content = ""
    combined_metadata = {}

    for _, doc in enumerate(filtered_docs):
        # Safely retrieve and concatenate page_content
        if hasattr(doc, 'page_content') and doc.page_content:
            combined_page_content += doc.page_content + "\n\n"
        
        # Safely merge metadata
        if hasattr(doc, 'metadata') and isinstance(doc.metadata, dict):
            combined_metadata.update(doc.metadata)

    # Remove trailing newlines
    combined_page_content = combined_page_content.strip()

    # Create and return a new Document
    return Document(
        page_content=combined_page_content,
        metadata=combined_metadata
    )

if __name__ == '__main__':
    uploaded_file_name = 'sample_pdf/invoice.pdf'
    # Open the file in binary mode and read its content
    with open(uploaded_file_name, 'rb') as f:
         pdf_data = f.read()
    # Convert byte data to a file-like object using io.BytesIO
    pdf_file = io.BytesIO(pdf_data)
    
    # Extract text from the uploaded PDF
    load_pdf(pdf_file, uploaded_file_name)
    doc = get_context('fetch me invoice details', uploaded_file_name)
    print(doc)