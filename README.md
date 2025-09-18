<h1 style="border: none;">Browser Automation using LLM</h1>


## 🚀 Overview

Browser Automation using LLM is a Python-based core framework that leverages the OpenAI API to control web pages using natural language. It uses Selenium to emulate human browser actions and a specially crafted JSON representation of the DOM to minimize token usage while providing enough context to the LLM. The project includes features like command tracking, history, error handling (where the AI can understand and fix errors), and an iteration limiter to ensure robust and efficient automation.

This project serves as a powerful foundation for building browser automation solutions using natural language. Developers can use this system to create tools, extensions, or applications without having to build the underlying architecture from scratch.

## 🛠️ Technologies Used

- **Python**: 3.12.6
- **Selenium**: For browser automation
- **openai**: OpenAI API integration
- **BeautifulSoup 4**: HTML parsing
- **html_to_json**: Converting HTML content into structured JSON
- **keyboard**: For keyboard interaction emulation

Configuration files:
- `requirements.txt`: For installing dependencies
- `.env`: Contains API keys and settings  
  Example contents:
  ```
  OPENAI_API_KEY_CLIENT=api_key
  OPENAI_API_KEY=api_key
  model=gpt-5
  start_url=https://google.com
  ERROR_THRESHOLD=5
  ```


## ⚙️ Installation

### Prerequisites

- Python 3.12.6 installed
- Browser drivers required by Selenium (like ChromeDriver or geckodriver)

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/username/browser-automation-using-llm.git
   ```
2. Navigate into the project directory:
   ```bash
   cd browser-automation-using-llm
   ```
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows use `venv\Scripts\activate`
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Configure your `.env` file with the appropriate API keys and settings.

6. Run the project:
   ```bash
   python main.py
   ```

## 🧪 Usage

After running the application, you can interact with it through the command line. You can:
- Enter commands to control the browser using natural language
- Type `help` to view available commands
- Type `exit` to quit the program

The tool tracks commands and errors, allowing the AI to understand and fix issues dynamically during operation.

## 🧑‍🤝‍🧑 Contributing

Contributions are welcome! This is designed as a core framework that others can build on to create their own browser automation solutions powered by natural language. Feel free to fork the repository, extend its functionality, and submit pull requests. Open issues if you encounter bugs or have suggestions.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## 📬 Contact

For questions or feedback, reach out via email: [username.praveen.email@gmail.com](mailto:username.praveen.email@gmail.com)
