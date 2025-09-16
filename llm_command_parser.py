from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import json
import html_to_json
from bs4 import BeautifulSoup, Tag
import time
import keyboard 


class LLMCommandParser:
    def __init__(self, url: str, usr_dir: str):
        options = webdriver.ChromeOptions()
        options.add_argument(f"--user-data-dir={usr_dir}")
        options.add_argument("--log-level=3")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_argument("disable-logging")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install(), log_path="NUL"),
            options=options,
        )
        self.goto(url)

        self.page_html = self.driver.page_source

        self.selector_map = {}


    def page_source_parser(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        self.selector_map = {}  # Reset selector map
        element_counter = [0]   # Counter for assigning unique element IDs

        ESSENTIAL_CONTENT_TAGS = {
            "html", "body", "button", "a", "label", "input", "textarea", "select", "option",
            "span", "div", "h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "form", "img", "nav",
            "section", "article", "table", "thead", "tbody", "tr", "td", "th", "ul", "ol",
            "iframe", "video", "audio", "i", "canvas"
        }

        ESSENTIAL_ATTRIBUTES = {
            "id", "class", "name", "type", "value", "href", "alt", "title", "role", "placeholder",
            "onclick", "onchange", "for", "selected", "checked", "min", "max", "step", "data-value",
            "aria-label", "aria-hidden", "data-testid"
        }

        def prune_element(el: Tag):
            for child in list(el.contents):
                if isinstance(child, Tag):
                    if child.name not in ESSENTIAL_CONTENT_TAGS:
                        child.decompose()
                    else:
                        prune_element(child)
            el.attrs = {k: v for k, v in el.attrs.items() if k in ESSENTIAL_ATTRIBUTES}

        for tag in soup(["script", "style"]):
            tag.decompose()

        prune_element(soup.body)

        def build_selector(el: Tag):
            parts = []
            while el and el.name != '[document]':
                part = el.name
                if el.has_attr('id'):
                    part += f"#{el['id']}"
                elif el.has_attr('class'):
                    classes = [cls for cls in el['class'] if cls.strip()]
                    if classes:
                        part += '.' + '.'.join(classes)
                else:
                    if el.parent:
                        siblings = [sib for sib in el.parent.find_all(el.name, recursive=False)]
                        index = siblings.index(el) + 1
                        part += f":nth-of-type({index})"
                parts.insert(0, part)
                el = el.parent
            return ' > '.join(parts)

        def assign_element_ids(el: Tag):
            selector = build_selector(el)
            el['_element_id'] = element_counter[0]
            self.selector_map[element_counter[0]] = selector
            element_counter[0] += 1

            # Add idx based on order among all siblings (not just same tag)
            if el.parent:
                all_element_siblings = [c for c in el.parent.contents if isinstance(c, Tag)]
                el['idx'] = str(all_element_siblings.index(el) + 1)

            for child in el.children:
                if isinstance(child, Tag):
                    assign_element_ids(child)

        assign_element_ids(soup.body)

        cleaned_html = str(soup.body)
        data = html_to_json.convert(cleaned_html)

        return json.dumps(data)


    # Core Action: Goto URL
    def goto(self, url: str):
        try:
            self.driver.get(url)
            
            # Wait until the document is fully loaded
            time.sleep(3)

            return "Command executed successfully"
        except Exception as e:
            return f"Error occurred while trying to execute command, Error: {type(e).__name__}"

    # Core Action: Click element by selector
    def click(self, element_id: int):
        try:
            selector = self.selector_map[element_id]
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            element.click()
            return "Command executed successfully"
        except Exception as e:
            return f"Error occurred while trying to execute command, Error: {type(e).__name__}"

    # Core Action: Fill input field
    def fill(self, element_id: int, text: str):
        selector = self.selector_map[element_id]
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            element.clear()
            element.send_keys(text)
            return "Command executed successfully"
        except Exception as e:
            return f"Error occurred while trying to execute command, Error: {type(e).__name__}"

    # Core Action: Scroll
    def scroll(self, direction="down", pixels=500):
        try:
            if direction == "down":
                self.driver.execute_script(f"window.scrollBy(0, {pixels});")
            elif direction == "up":
                self.driver.execute_script(f"window.scrollBy(0, -{pixels});")
            return "Command executed successfully"
        except Exception as e:
            return f"Error occurred while trying to execute command, Error: {type(e).__name__}"

    # Core Action: Extract text
    def extract(self, element_id: int):
        selector = self.selector_map[element_id]
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            return element.text
        except Exception as e:
            return f"Error occurred while trying to execute command, Error: {type(e).__name__}"
        
    def press_enter(self, element_id: int):
        selector = self.selector_map[element_id]
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            element.send_keys(Keys.ENTER)
            return "Command executed successfully"
        except Exception as e:
            return f"Error occurred while trying to execute command, Error: {type(e).__name__}"

    # Core Action: Wait for element to appear (basic sleep, can upgrade to WebDriverWait)
    def wait(self, seconds: int):
        try:
            time.sleep(seconds)
            return "Command executed successfully"
        except Exception as e:
            return f"Error occurred while trying to execute command, Error: {type(e).__name__}"

    # Core Action: Switch to next/previous tab
    def switch_tab(self, index: int):
        try:
            tabs = self.driver.window_handles
            if index < len(tabs):
                self.driver.switch_to.window(tabs[index])
                return "Command executed successfully"
            else:
                return f"Error: Tab index {index} out of range"
        except Exception as e:
            return f"Error occurred while trying to execute command, Error: {type(e).__name__}"

    # Core Action: Browser back/forward
    def navigate(self, direction: str):
        try:
            if direction == "back":
                self.driver.back()
            elif direction == "forward":
                self.driver.forward()
            return "Command executed successfully"
        except Exception as e:
            return f"Error occurred while trying to execute command, Error: {type(e).__name__}"

    def parse_and_execute(self, llm_output: str):
        try:
            command = json.loads(llm_output)
            action = command.get("action")
            if not action:
                print("❌ No 'action' field found.")
                return

            # Map actions to method argument unpacking
            method_args = {
                "click": ["element_id"],
                "fill": ["element_id", "text"],
                "scroll": ["direction", "pixels"],
                "screenshot": ["path"],
                "wait": ["seconds"],
                "navigate": ["direction"],
                "switch_tab": ["index"],
                "extract": ["element_id"],
                "goto": ["url"],
                "press_enter": ["element_id"],
                "move_slider": ["target_text", "target_value", "increment_mode" ,"slides_per_sec"],
                "get_coordinates": ["element_id"],
                "zoom": ["scan_name", "target_zoom", "direction"],
                "enter_fullscreen": ["scan_name"]
            }

            method = getattr(self, action, None)
            if not method:
                print(f"⚠️ Unknown action: {action}")
                return

            # Extract only the arguments that method needs
            args = [command.get(arg) for arg in method_args.get(action, [])]

            # Call the method with extracted arguments
            result = method(*args)

            current_page_html = self.page_source_parser(self.driver.page_source)

            if len(self.driver.window_handles) > 1:
                current = self.driver.current_window_handle
                all_tabs = self.driver.window_handles

                # Find the new tab handle (the one that's NOT the current one)
                new_tab = [handle for handle in all_tabs if handle != current][0]

                # Switch to the new tab
                self.driver.switch_to.window(new_tab)

                # Close the old tab
                self.driver.switch_to.window(current)
                self.driver.close()

                # Switch back to the new tab (since old one is closed)
                self.driver.switch_to.window(new_tab)
                time.sleep(5)
            
            script = """
            document.querySelectorAll("input, textarea, select").forEach(el => {
                if (el.tagName.toLowerCase() === "select") {
                    el.setAttribute("data-value", el.options[el.selectedIndex]?.text || "");
                } else {
                    el.setAttribute("data-value", el.value || "");
                }
            });
            """
            self.driver.execute_script(script)

            time.sleep(1.5)


            return result

        except json.JSONDecodeError:
            print("❌ Failed to parse LLM output as JSON.")
        except Exception as e:
            print(f"❌ Error during execution: {e}")

    # Cleanup
    def close(self):
        self.driver.quit()
