import streamlit as st
import uuid
from rag_chat_bot import chat
# Function to process user input and generate bot responses based on the selected document
# def chat(user_id, document, question):
#     # Replace this logic with your actual implementation for bot response
#     if question and document:
#         return f"Response to your question about '{document}': {question}"
#     else:
#         return "Unable to process your request. Please try again."

# Streamlit app
def main():
    st.title("Chatbot with Conversation History")
    
    # Generate a random user ID if not already set
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())

    # Display the user ID
    st.write(f"Your User ID: `{st.session_state.user_id}`")

    # Initialize session state for chat history and button state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "is_sending" not in st.session_state:
        st.session_state.is_sending = False  # Track if a request is being processed

    # Define the options
    options = ("Invoice", "Employee Handbook_Final_20.12.2022", "Nandkumar_Ghatage_Latest_CV")
    
    # Initialize selected_option with a valid default value
    if "selected_option" not in st.session_state:
        st.session_state.selected_option = options[0]  # Default to the first option

    # Step 1: Select an option and enter a question
    st.subheader("Select an option and ask a question")

    # Dropdown for selecting an option
    selected_option = st.selectbox(
        "Select an option:",
        options,
        index=options.index(st.session_state.selected_option),  # Default selection
        key="select_option"  # Track changes to the select box
    )

    # Display chat history
    st.subheader("Chat History")
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f"**You:** {message['message']}")
        else:
            st.markdown(f"**Bot:** {message['message']}")

    # Text input for user question at the bottom
    user_input = st.text_input("Type your question here...", value="", key="user_input")

    # Submit button (grayed out if a request is being processed)
    if st.button("Send", disabled=st.session_state.is_sending):
        if user_input.strip():
            # Disable the button to prevent multiple clicks
            st.session_state.is_sending = True

            # Append user message and selected option to chat history
            st.session_state.chat_history.append({
                "role": "user",
                "message": user_input,
                "option": selected_option
            })

            # Debugging: Log input to check
            #st.write(f"Debug: User ID: {st.session_state.user_id}, Document: {selected_option}, Question: {user_input}")

            # Generate bot response based on the selected document
            if selected_option == "Invoice":
                bot_response = chat(st.session_state.user_id, "invoice.pdf", user_input)
            elif selected_option == "Employee Handbook_Final_20.12.2022":
                bot_response = chat(st.session_state.user_id, "Employee Handbook_Final_20.12.22.pdf", user_input)
            elif selected_option == "Nandkumar_Ghatage_Latest_CV":
                bot_response = chat(st.session_state.user_id, "Nandkumar_Ghatage_Latest_CV.pdf", user_input)
            else:
                bot_response = "I'm not sure what you're interested in. Please try again."

            # Debugging: Log bot response
            #st.write(f"Debug: Bot Response: {bot_response}")

            # Append bot response to chat history
            st.session_state.chat_history.append({"role": "bot", "message": bot_response})

            # Re-enable the button after the response is generated
            st.session_state.is_sending = False

            # Clear the input field by rerunning the app
            st.rerun()

# Run the Streamlit app
if __name__ == "__main__":
    main()
