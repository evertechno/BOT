import streamlit as st
import google.generativeai as genai
import json
import os

# Configure the API key securely from Streamlit's secrets
# Ensure GOOGLE_API_KEY is added in secrets.toml (for local) or Streamlit Cloud Secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Streamlit App UI
st.title("Instant Bot Builder")
st.write("Create your own AI-powered bot for various purposes like sales, support, and social media management.")

# Step 1: Choose a bot template
bot_templates = {
    "Sales Bot": "This bot helps engage customers and drive sales through personalized interactions.",
    "Support Bot": "This bot assists in customer support, answering queries and troubleshooting problems.",
    "Social Media Bot": "This bot manages and interacts with social media accounts, posting updates and responding to comments."
}

# Dropdown for selecting the bot template
selected_template = st.selectbox("Select a Bot Template:", list(bot_templates.keys()))

# Step 2: Customize bot settings
if selected_template:
    st.subheader(f"Customize Your {selected_template}")
    if selected_template == "Sales Bot":
        tone = st.radio("Choose the tone of the bot:", ["Friendly", "Professional", "Casual"])
        primary_goal = st.selectbox("Select the primary goal:", ["Lead Generation", "Product Inquiry", "Customer Retention"])
    elif selected_template == "Support Bot":
        response_type = st.selectbox("Select response type:", ["FAQ", "Troubleshooting", "Product Issues"])
        urgency_level = st.radio("Response urgency level:", ["Immediate", "Within an hour", "End of the day"])
    elif selected_template == "Social Media Bot":
        interaction_type = st.selectbox("Select interaction type:", ["Post Scheduling", "Comment Replying", "DM Responses"])
        platform = st.selectbox("Select platform:", ["Instagram", "Twitter", "Facebook"])

# Step 3: Generate bot script
if st.button("Generate Bot"):
    try:
        # Prepare the prompt based on user input
        prompt = f"Create a bot for {selected_template}. "
        
        # Add customizations to the prompt
        if selected_template == "Sales Bot":
            prompt += f"The bot should have a {tone} tone and focus on {primary_goal}."
        elif selected_template == "Support Bot":
            prompt += f"The bot should handle {response_type} with a response urgency of {urgency_level}."
        elif selected_template == "Social Media Bot":
            prompt += f"The bot should focus on {interaction_type} on {platform}."
        
        # Generate the bot's script using Gemini's model
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        # Display the bot's script
        st.subheader("Generated Bot Script:")
        bot_script = response.text
        st.write(bot_script)
        
        # Step 4: Test the generated bot
        st.subheader("Test Your Bot:")
        user_input = st.text_input("Ask your bot a question:", "What is your return policy?")
        if user_input:
            bot_response = model.generate_content(f"Bot script: {bot_script} User input: {user_input}")
            st.write(f"Bot's Response: {bot_response.text}")
        
        # Step 5: Save and Export Bot
        save_button = st.button("Save Bot Script")
        if save_button:
            # Save bot script to a file (JSON format)
            bot_name = st.text_input("Enter a name for your bot:", "MyBot")
            if bot_name:
                bot_data = {
                    "name": bot_name,
                    "template": selected_template,
                    "customizations": {
                        "tone": tone if selected_template == "Sales Bot" else None,
                        "primary_goal": primary_goal if selected_template == "Sales Bot" else None,
                        "response_type": response_type if selected_template == "Support Bot" else None,
                        "urgency_level": urgency_level if selected_template == "Support Bot" else None,
                        "interaction_type": interaction_type if selected_template == "Social Media Bot" else None,
                        "platform": platform if selected_template == "Social Media Bot" else None
                    },
                    "script": bot_script
                }
                
                # Export the bot to a JSON file
                file_name = f"{bot_name}.json"
                with open(file_name, 'w') as f:
                    json.dump(bot_data, f, indent=4)
                st.success(f"Bot '{bot_name}' saved successfully as {file_name}")
                
                # Provide option to download the file
                with open(file_name, "r") as file:
                    st.download_button(label="Download Bot Script", data=file, file_name=file_name, mime="application/json")
                
                # Option to remove file after download
                os.remove(file_name)
        
    except Exception as e:
        st.error(f"Error: {e}")
