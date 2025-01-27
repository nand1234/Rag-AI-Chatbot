import os
import redis
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEndpoint
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
from duckduckgo_search import DDGS
from langchain.memory import ConversationBufferMemory
from langchain import hub
from embedding import get_context
from langchain.schema import HumanMessage

import warnings
warnings.filterwarnings("ignore")

# Set up Redis
redis_client = redis.Redis(host="localhost", port=6380, db=0)

# Function to get or create user session
def get_user_session(user_id):
    return RedisChatMessageHistory(
        session_id=f"user:{user_id}",  # Unique session ID per user
        url="redis://localhost:6380/0"  # Redis connection URL
    )

# Function to perform DuckDuckGo search
def search_web(query):
    ddgs = DDGS()
    results = ddgs.text(query, max_results=3)  # Fetch top 3 results
    formatted_results = []
    for result in results:
        title = result.get("title", "No title available")
        link = result.get("link", "No link available")
        formatted_results.append(f"{title}: {link}")
    return "\n".join(formatted_results)

# Function to initialize the chatbot
def initialize_chatbot(user_id):
    # Set up memory with Redis
    memory = ConversationBufferMemory(
        chat_memory=get_user_session(user_id),
        memory_key="chat_history",
        return_messages=True
    )

    # Set up Hugging Face LLM
    llm = HuggingFaceEndpoint(
        endpoint_url="https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2",  # Replace with your model endpoint
        temperature=0.7,
    )

    # Set up web search tool
    search_tool = Tool(
        name="Web Search",
        func=search_web,
        description="Useful for searching the web for up-to-date information."
    )

    # Load the default ReAct prompt template
    prompt = hub.pull("hwchase17/react")

    # Set up conversation chain with tools
    tools = [search_tool]
    agent = create_react_agent(
        tools=tools,
        llm=llm,
        prompt=prompt,
    )

    # Create AgentExecutor with memory
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=False,  # Set to False to hide agent thoughts
        handle_parsing_errors=True  # Handle parsing errors gracefully
    )

    return agent_executor

# Function to chat with the bot
def chat(user_id, metadata, user_input):
    # Initialize chatbot for the user
    agent = initialize_chatbot(user_id)

    # Get the relevant document text
    response = get_context(user_input, metadata)
    content = response.page_content
    meta_data = response.metadata

    # Create the HumanMessage object
    message = HumanMessage(
        content=content,
        metadata=meta_data
    )

    # Define a prompt template with context
    prompt_template = PromptTemplate(
        input_variables=["user_input", "chat_history", "message"],
        template="""
        You are a helpful and friendly assistant. If context is not available, politely steer the conversation back to previous chat history.
        You have access to a search tool to provide accurate and up-to-date information.

        **Context:**
        {message}

        **Conversation History:**
        {chat_history}

        **User Input:**
        {user_input}

        **Assistant:"""
    )

    # Format the prompt with the appropriate variables
    formatted_prompt = prompt_template.format(
        user_input=user_input,
        chat_history=agent.memory.buffer,
        message=message.content
    )

    try:
        # Get the bot's response
        response = agent.invoke({"input": formatted_prompt})
        print(f"Bot: {response['output']}")
        return response['output']
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Sorry, I encountered an error while processing your request."

# Main loop for chatting
if __name__ == "__main__":
    user_id = "user_123"  # Replace with a unique user ID
    print("Chatbot is ready! Type 'exit' to end the chat.")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break
        metadata = "sample_pdf/Nandkumar_Ghatage_Latest_CV.pdf"
        # Generate an answer using the documents retrieved from the vector store
        chat(user_id, metadata, user_input)