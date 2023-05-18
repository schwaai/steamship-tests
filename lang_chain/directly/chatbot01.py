from langchain import LLMChain, PromptTemplate
from steamship import Steamship
# from langchain import OpenAI
from steamship_langchain import OpenAI
import steamship_langchain as ssl
from steamship_langchain.llms import OpenAIChat
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
#from langchain.chains.
from steamship_langchain.memory import ChatMessageHistory

import logging

logging.disable(logging.CRITICAL)  # disable warning messages to declutter

template = """Assistant is a large language model trained by OpenAI.

Assistant is designed to be able to assist with a wide range of tasks, from answering simple questions to providing 
in-depth explanations and discussions on a wide range of topics. As a language model, Assistant is able to generate 
human-like text based on the input it receives, allowing it to engage in natural-sounding conversations and provide 
responses that are coherent and relevant to the topic at hand.

Assistant is constantly learning and improving, and its capabilities are constantly evolving. It is able to process 
and understand large amounts of text, and can use this knowledge to provide accurate and informative responses to a 
wide range of questions. Additionally, Assistant is able to generate its own text based on the input it receives, 
allowing it to engage in discussions and provide explanations and descriptions on a wide range of topics.

Overall, Assistant is a powerful tool that can help with a wide range of tasks and provide valuable insights and 
information on a wide range of topics. Whether you need help with a specific question or just want to have a 
conversation about a particular topic, Assistant is here to assist.

############-{history}-####################
Human: {human_input}
Assistant: """
client = Steamship()
prompt = PromptTemplate(input_variables=["history", "human_input"], template=template)

import string
import random

# initializing size of string
N = 10

# using random.choices()
# generating random strings
rand_key = ''.join(random.choices(string.ascii_lowercase, k=N))
chat_memory = ChatMessageHistory(client=client, key=rand_key)

chatgpt_chain = LLMChain(
    llm=OpenAIChat(client=client, model_name="gpt-4", temperature=0),
    prompt=prompt,
    verbose=True,
    memory=ConversationBufferWindowMemory(chat_memory=chat_memory, k=2),

)

response = chatgpt_chain.predict(
    human_input="I want you to act as a Linux terminal. I will type commands and you will reply with what the \n"
                "terminal should show. I want you to only reply with the terminal output inside one unique code \n"
                "block, and nothing else. Do not write explanations. Do not type commands unless I instruct you to do \n"
                "so. When I need to tell you something in English I will do so by putting text inside curly brackets \n"
                "{like this}. My first command is pwd. "
)
while True:
    human_input = input("Enter your command or 'exit' to quit: ")
    if human_input.strip().lower() == 'exit':
        break
    else:
        response = chatgpt_chain.predict(human_input=human_input)
        print(response)

