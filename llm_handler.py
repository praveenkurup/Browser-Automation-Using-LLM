import json
import os
import platform
import subprocess
import threading
from dotenv import load_dotenv
from openai import OpenAI
from llm_command_parser import LLMCommandParser
import time
import itertools
import sys
from contextlib import contextmanager, redirect_stdout
from queue import Queue
import keyboard
import io


ERROR_THRESHOLD = os.getenv("ERROR_THRESHOLD")
error_sound = "./sound effects/error.wav"
sucess_sound = "./sound effects/success.wav"
step_sucess_sound = "./sound effects/step_success.wav"


@contextmanager
def spinner(message="Processing", status_getter=None):
    stop_event = threading.Event()
    max_length = 100
    result_status = {"symbol": "✅"}

    def spin():
        truncated = (message[:max_length] + '...') if len(message) > max_length else message
        padding = ' ' * 20
        for symbol in itertools.cycle(['|', '/', '-', '\\']):
            if stop_event.is_set():
                break
            sys.stdout.write(f'\r{truncated} {symbol}{padding}')
            sys.stdout.flush()
            time.sleep(0.1)

        if status_getter:
            status = status_getter()
            if isinstance(status, str) and "error occurred" in status.lower():
                result_status["symbol"] = "❌"
        sys.stdout.write(f'\r{truncated} {result_status["symbol"]}{padding}\n')
        sys.stdout.flush()

    thread = threading.Thread(target=spin)
    thread.daemon = True
    thread.start()

    try:
        f = io.StringIO()
        with redirect_stdout(f):
            yield
    finally:
        stop_event.set()
        thread.join()


# --- Load environment variables ---
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -- Config --
MODEL_NAME = os.getenv("model")
CHROME_USER_DATA = os.path.join(os.getcwd(), "/profile")
BROWSER_START_URL = os.getenv("start_url")

# --- Init ---
prompt_history = []
stop_requested = False  # Global flag to break loop


def build_prompt(prompt_history, command_history, url, page_data, user_request="", CURRENT_FULLSCREEN_SCAN=""):
    prompt = f"""
    You are a browser automation assistant. Your goal is to complete the **user's request** by returning one or more browser actions in the correct order.

    🧑‍💻 User's Request:
    {user_request}

    📓 Previous User Prompts:
    {json.dumps(prompt_history)}

    VERY IMPORTANT INSTRUCTION:
    - Never send 2 or more actions until its to fill a input form and then press a button.
    - Always check command history and check if the action you are going to send is there or not, if yes and executed without errors, then don't send that action, either continue with the next action from user request or send done.

    ---
    🛠️ Available Actions:

    1. click  
    - Clicks an element on the page.  
    - Example: {{ "action": "click", "element_id": 42, "intend": "Click the submit button" }}

    2. fill  
    - Fills text into an input field.  
    - Example: {{ "action": "fill", "element_id": 17, "text": "user@example.com", "intend": "Fill in the email input" }}

    3. scroll  
    - Scrolls the page.  
    - Example: {{ "action": "scroll", "direction": "down", "pixels": 500, "intend": "Scroll down to find more content" }}

    4. wait  
    - Waits for a duration.  
    - Example: {{ "action": "wait", "seconds": 3, "intend": "Wait for animations or content to load" }}

    5. navigate  
    - Navigates browser history.  
    - Example: {{ "action": "navigate", "direction": "back", "intend": "Go back to the previous page" }}

    6. goto  
    - Navigates to a specific URL.  
    - Example: {{ "action": "goto", "url": "https://example.com/login", "intend": "Open the login page" }}

    7. press_enter  
    - Sends Enter key to an input.  
    - Example: {{ "action": "press_enter", "element_id": 19, "intend": "Submit the search form" }}

    12. done  
    - Signals task completion.  
    - Example: {{ "action": "done", "intend": "The requested task was successfully completed" }}

    ---
    ✅ IMPORTANT RULE:

    **Always use the `element_id` field from the DOM (in `page_data`) to refer to elements.**  
    Each element has a unique `element_id` corresponding to an internal CSS selector. Do not try to guess or generate selectors yourself.  

    When acting on a specific element:
    - Find the right element based on visible text, tag, or attributes.
    - Use its `element_id` when returning any action.

    If you cannot find a matching element:
    - Respond with "element not found" and do not run any action.

    ---
    📌 DOM Matching Requirements:

    - Use only `element_id` values from `page_data`.
    - Never guess or invent any selectors.
    - Each `element_id` corresponds internally to a real `_selector`.

    ---

    🧠 Contextual Knowledge (Use When Relevant):

    - Try to avoid sending multiple actions as much as possible.. ONLY and ONLY use it for filling up inputs and pressing submit.

    ---
    🌐 Current Page URL:
    {url}

    📜 Command History (latest last):
    {json.dumps(command_history)}

    🧩 DOM Snapshot:
    {page_data}

    ---
    Before you respond:
    2. Only return new actions if they are clearly needed
    3. Otherwise, return:
    {{ "action": "done", "intend": "All steps from the user request were already completed" }}


    ⛔ Do NOT wrap your output in markdown. Return a raw JSON **list** of action objects.

    Now return the next action(s) to perform.
    """
    return prompt



def query_llm(prompt):
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You control a web browser using JSON commands. Do not use natural language.\n"
                    'If the task appears to be completed already based on the DOM or last command result, return { "action": "done" } immediately. '
                    "Only take actions if you are confident they are still necessary."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    return response.choices[0].message.content.strip()

stop_requested = False

def stop_task():
    global stop_requested
    stop_requested = True
    print("\n⏹️ Stop requested via ESC key.\n")

    
def _play_sound(sound_file):
    if platform.system() == "Windows":
        subprocess.Popen(['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', sound_file])
    else:
        subprocess.Popen(['afplay', sound_file])  # macOS


def main(main_queue: Queue):
    global stop_requested, CURRENT_FULLSCREEN_SCAN
    
    keyboard.add_hotkey("esc", stop_task)
    task_queue = main_queue
    agent = LLMCommandParser(url=BROWSER_START_URL, usr_dir=CHROME_USER_DATA)
    error_counter = 0

    # --- Main Loop ---
    try:
        while True:
                task = task_queue.get()

                if task.lower() == "exit":
                    agent.driver.quit()
                    break

                print(f"\n🚀 Starting task: {task}")
                done = False
                stop_requested = False
                command_history = []
                prompt_history.append(task)

                while not done:
                    if stop_requested:
                        print("⏹️ Task interrupted by hotkey.")
                        break
                        
                    if error_counter >= ERROR_THRESHOLD:
                        print("Consecutive errors exceeded threshold, stopping task!")
                        break


                    current_html = agent.driver.page_source
                    dom_data = agent.page_source_parser(current_html)

                    prompt = build_prompt(
                        prompt_history=prompt_history,
                        command_history=command_history,
                        url=agent.driver.current_url,
                        page_data=dom_data,
                        user_request=task,
                    )

                    llm_output = (
                        query_llm(prompt).strip().replace("```json", "").replace("```", "")
                    )

                    # print("\n\nLLM OUTPUT!", llm_output, "\n\n")
                    try:
                        actions = json.loads(llm_output)
                        if not isinstance(actions, list):
                            actions = [actions]
                    except Exception as e:
                        print(f"\n❌ Failed to parse LLM output: {e}")
                        print(f"🧾 Raw output:\n{llm_output}")
                        break

                    for action in actions:
                        if action.get("action", "").lower() == "done":
                            done = True
                            break

                        result_container = {"result": ""}

                        def get_status():
                            return result_container["result"]

                        with spinner(
                            f"🤖 Executing: {action.get('intend', action['action'])} {"Press p to stop slider" if action.get('action', action['action']) == "move_slider" else ""}",
                            status_getter=get_status,
                        ):
                            try:
                                result = agent.parse_and_execute(
                                    json.dumps(action)
                                )
                                print(f"\nResults is {result}")
                            except Exception as e:
                                print("Some error happened!")
                                result = "Error occurred while trying to execute command"
                                print(f"\nResults is {result}, {e}")
                            result_container["result"] = result or ""


                        command_history.append({"command": action, "result": result})

                        if "Error occurred while trying to execute command".lower() in result.lower():
                            _play_sound(error_sound)
                            error_counter += 1
                        else:
                            _play_sound(step_sucess_sound)
                            error_counter = 0

                    time.sleep(1.2)

                if error_counter < ERROR_THRESHOLD and not stop_requested:
                    _play_sound(sucess_sound)
                    print(f"✅ {task} — Task Completed!\n")
                error_counter = 0

    except KeyboardInterrupt:
        print("\n👋 Exiting automation.")

    finally:
        agent.close()
