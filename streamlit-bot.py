import streamlit as st
import uuid
from rag_chat_bot import chat
from embedding import load_pdf
import io
import time

# Initialize session state for chat history and file upload
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())  # Generate a unique user ID

if "is_sending" not in st.session_state:
    st.session_state.is_sending = False

if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None

# Function to simulate typing effect
def typing_effect_in_chat(bot_response: str, delay: float = 0.05):
    """Simulate typing effect while displaying the bot response."""
    placeholder = st.empty()  # Temporary placeholder for the typing effect
    bot_message = ""
    for char in bot_response:
        bot_message += char
        placeholder.markdown(f"**Bot:** {bot_message}")
        time.sleep(delay)
    # Once typing is complete, add the full message to chat history
    st.session_state.chat_history.append({"role": "bot", "message": bot_response})
    placeholder.empty()  # Clear the placeholder after completion

# Streamlit app
def main():
    st.title("Chatbot with Conversation History")
    
    # File upload logic
    uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
    if uploaded_file is not None:
        # Only load the file if it's not already processed
        if st.session_state.uploaded_file_name != uploaded_file.name:
            byte_data = uploaded_file.read()
            pdf_file = io.BytesIO(byte_data)
            
            # Process the uploaded file
            try:
                status = load_pdf(pdf_file, uploaded_file.name)
                st.session_state.uploaded_file_name = uploaded_file.name
                st.success(f"File '{uploaded_file.name}' processed successfully!")
            except Exception as e:
                st.error(f"Failed to process the file: {e}")

    # Dropdown options
    predefined_options = ["Invoice", "Employee Handbook_Final_20.12.2022", "Nandkumar_Ghatage_Latest_CV"]
    dropdown_options = predefined_options + ([uploaded_file.name] if uploaded_file else [])

    # Dropdown for selecting an option
    selected_option = st.selectbox("Select an option:", dropdown_options, key="select_option")

    # Display chat history
    st.subheader("Chat History")
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f"**You:** {message['message']}")
        else:
            st.markdown(f"**Bot:** {message['message']}")

    # User question input
    user_input = st.text_input("Type your question here...", value="", key="user_input")

    # Submit button
    if st.button("Send", disabled=st.session_state.is_sending):
        if user_input.strip():
            st.session_state.is_sending = True

            # Add user message to chat history
            st.session_state.chat_history.append({
                "role": "user",
                "message": user_input,
                "option": selected_option,
            })

            # Determine the bot response based on the selected option
            if selected_option in predefined_options:
                bot_response = chat(st.session_state.user_id, f"{selected_option}.pdf", user_input)
            elif selected_option == uploaded_file.name:
                bot_response = chat(st.session_state.user_id, uploaded_file.name, user_input)
            else:
                bot_response = "I'm not sure what you're referring to. Please try again."

            # Add bot response with typing effect
            typing_effect_in_chat(bot_response)

            # Re-enable the button after processing
            st.session_state.is_sending = False

            # Clear user input by rerunning the app
            st.rerun()
        else:
            st.warning("Please enter a question before sending.")

# Run the Streamlit app
if __name__ == "__main__":
    main()
