import os
from typing import Any, Dict

import streamlit as st
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_community.agent_toolkits.load_tools import load_tools
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain_community.chat_message_histories import \
    StreamlitChatMessageHistory
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI


def create_agent_chain():
    chat = ChatOpenAI(
        model_name=os.getenv("OPENAI_MODEL_NAME"),
        temperature=float(os.getenv("OPENAI_TEMPERATURE")),
    )
    tools = load_tools(["ddg-search", "wikipedia"])
    prompt = hub.pull("hwchase17/openai-tools-agent")
    agent = create_openai_tools_agent(chat, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools)
    
def main():
    st.title("langchain-streamlit-app")
    history = StreamlitChatMessageHistory()
    for message in history.messages:
        message: BaseMessage # type: ignore 
        st.chat_message(message.type).write(message.content)

    prompt = st.chat_input("input")
    if prompt:
        with st.chat_message("user"):
            history.add_user_message(prompt)
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            callback = StreamlitCallbackHandler(st.container())
            agent_chain = create_agent_chain()
            response = agent_chain.invoke(
                {"input": prompt},
                {"callbacks": [callback]},
            )
            history.add_ai_message(response["output"])
            st.markdown(response['output'])
    
        
if __name__ == "__main__":
    main()