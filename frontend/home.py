import base64

import streamlit as st
from web_utils import initialize_page


def main():
    initialize_page(title="Hyperstack - LLM Inference Toolkit")

    image_path = "./media/hyperstack-computer.jpg"
    image_src = f'data:image/png;base64,{base64.b64encode(open(image_path, "rb").read()).decode()}'

    st.markdown(
        f"""
    <div style="display:inline-block;">
    <h3> Introduction </h3>
    <img src="{image_src}" width="40%" alt="Image" style="float:right; margin-left:20px; margin-right:20px;
    margin-top:0px;">
    <p>This open-source app allows users to easily get started with Large Language Models (LLMs) on Hyperstack. It offers a complete toolkit for deploying, managing, and prototyping LLMs, making it simple to deploy multiple models simultaneously and generate API keys for integration. Additionally, it features a unified proxy API that handles all requests, streamlining interactions with different models. Whether you're testing LLMs or integrating them into your projects, this app provides the tools and flexibility you need to accelerate your workflow.</p>

    <p><b>Disclaimer:</b> This app is open-source and provided as-is. While it includes a range of useful features, it is the user's responsibility to ensure proper security and compliance. NexGen Cloud and/or Hyperstack are not liable for any security vulnerabilities or issues that may arise from its use.</p>
    <h3> Usage </h3>
    <p>To get started, navigate to the sidebar and select the desired page. You can choose from the following options:</p>
    <ul>
    <li><b>🏠 Home:</b> Return to the home page.</li>
    <li><b>📦 Models:</b> View all deployed LLMs, add new models, and manage replicas for each model.</li>
    <li><b>👩‍💻 Playground:</b> Interact with your deployed LLM models.</li>
    <li><b>🔑 API Keys:</b> Create and manage API keys for your users.</li>
    <li><b>📊 Monitoring:</b> View and interact with the data stored in your databases.</li>
    </ul>
    <br>

    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
