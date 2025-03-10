AI Chatbot for Property Search
==================================

This project is an AI-powered chatbot that helps users search for properties using 
natural language processing (NLP) and speech recognition. The chatbot is built with 
OpenAI's API, Tkinter GUI, and Pandas for data handling.

----------------------------------
🚀 Features:
----------------------------------
✅ Accepts both **text-based and voice-based** queries.  
✅ Uses OpenAI API for Natural Language Processing (NLP).  
✅ Interactive **Tkinter GUI**.  
✅ Reads property filter data from an Excel file (`filter_data.xlsx`).  
✅ Parses user queries into structured search parameters.  

----------------------------------
🛠️ Setup Instructions:
----------------------------------

1️⃣ Clone the Repository  
----------------------
Open **Git Bash** (Windows) or **Terminal** (Mac/Linux) and run:
```
git clone https://github.com/kincaidclan/ai-chatbot.git
cd ai-chatbot
```

2️⃣ Set Up the OpenAI API Key  
----------------------
This project requires an **OpenAI API key** to process user queries.

🔑 Get an OpenAI API Key:
- Go to: https://platform.openai.com/signup/
- Sign in or create an account.
- Click **Create API Key** and copy it.

🌎 Add API Key as an Environment Variable:
- **Windows (Command Prompt / Git Bash)**
  ```
  echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.bashrc
  source ~/.bashrc
  ```

- **Mac/Linux**
  ```
  echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.bash_profile
  source ~/.bash_profile
  ```

- **For Temporary Use** (Works until you close the terminal session)
  ```
  export OPENAI_API_KEY="your-api-key-here"
  ```

3️⃣ Install Dependencies  
----------------------
Make sure you have **Python 3.8+** installed. Then, install required libraries:

```
pip install -r requirements.txt
```

If `requirements.txt` does not exist, install manually:

```
pip install openai pandas tkinter pillow speechrecognition
```

4️⃣ Run the Chatbot  
----------------------
Once everything is set up, launch the chatbot:

```
python ai-chatbot.py
```

This will open the **Tkinter GUI**, where you can:
- **Type a query** or **use voice input** 🎤.
- The chatbot will **process the query** and return structured results.

----------------------------------
📝 How the Chatbot Works:
----------------------------------
- The chatbot **accepts both text and voice-based inputs**.
- If using text input, you can **type your request** in the input box.
- If using voice input, click the **"Speak" button**, and the chatbot will listen to your query.
- The chatbot then processes the input using **OpenAI’s NLP**.
- It **extracts relevant filters** and **matches them with property data**.
- The response is displayed in the **output area** of the GUI.

----------------------------------
📂 Project Structure:
----------------------------------
```
ai-chatbot/
│── ai-chatbot.py        # Main Python script for the chatbot
│── filter_data.xlsx     # Property filter data (Excel)
│── requirements.txt     # Python dependencies
│── README.txt           # Documentation
```

----------------------------------
🔧 Troubleshooting:
----------------------------------
1️⃣ **OpenAI API Key Not Found**
- Error Message: `openai.error.AuthenticationError: Incorrect API key provided`
- Solution: Run:
  ```
  echo $OPENAI_API_KEY
  ```
  If empty, **re-add your API key** (see Step 2).

2️⃣ **Missing Python Libraries**
- If you get an `ImportError`, install dependencies:
  ```
  pip install -r requirements.txt
  ```

----------------------------------
📧 Contact:
----------------------------------
👨‍💻 **GitHub:** https://github.com/kincaidclan  
📬 **Email:** nolanckincaid@gmail.com 
💼 **LinkedIn:** https://www.linkedin.com/in/nolan-kincaid-8b60281a5

🎉 Now Your AI Chatbot is Ready to Go! 🚀  
