import os
import re
import json
import threading
import pandas as pd
from difflib import get_close_matches
from openai import OpenAI
import tkinter as tk
from tkinter import StringVar, Listbox, Scrollbar, Label, messagebox, Toplevel, Entry, Frame, Button
from PIL import Image, ImageTk
from tkinter.scrolledtext import ScrolledText
import platform
import subprocess
import speech_recognition as sr

class SimpleYesNoDialog(Toplevel):
    def __init__(self, parent, title, prompt):
        super().__init__(parent)
        self.title(title)
        self.prompt = prompt
        self.result = None

        self.center_dialog(300, 120)
        self.transient(parent)
        self.grab_set()

        self.label = tk.Label(self, text=self.prompt, font=("Arial", 12), wraplength=280)
        self.label.pack(pady=10)

        self.button_frame = tk.Frame(self)
        self.button_frame.pack(pady=5)

        self.yes_button = tk.Button(self.button_frame, text="Yes", width=10, command=self.on_yes)
        self.yes_button.pack(side=tk.LEFT, padx=5)

        self.no_button = tk.Button(self.button_frame, text="No", width=10, command=self.on_no)
        self.no_button.pack(side=tk.LEFT, padx=5)

    def center_dialog(self, width, height):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def on_yes(self):
        self.result = True
        self.destroy()

    def on_no(self):
        self.result = False
        self.destroy()

    def get_result(self):
        self.wait_window()
        return self.result

def ask_yes_no(parent, title, prompt):
    dialog = SimpleYesNoDialog(parent, title, prompt)
    return dialog.get_result()


class AddNewDialog(Toplevel):
    def __init__(self, parent, title, prompt):
        super().__init__(parent)
        self.title(title)
        self.prompt = prompt
        self.result = None  # "add" or "new"

        self.center_dialog(400, 140)
        self.transient(parent)
        self.grab_set()

        self.label = tk.Label(self, text=self.prompt, font=("Arial", 12), wraplength=380)
        self.label.pack(pady=10)

        self.button_frame = tk.Frame(self)
        self.button_frame.pack(pady=5)

        self.add_button = tk.Button(self.button_frame, text="Add", width=10, command=self.on_add)
        self.add_button.pack(side=tk.LEFT, padx=5)

        self.new_button = tk.Button(self.button_frame, text="New", width=10, command=self.on_new)
        self.new_button.pack(side=tk.LEFT, padx=5)

    def center_dialog(self, width, height):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def on_add(self):
        self.result = "add"
        self.destroy()

    def on_new(self):
        self.result = "new"
        self.destroy()

    def get_result(self):
        self.wait_window()
        return self.result

def ask_add_new(parent, title, prompt):
    dialog = AddNewDialog(parent, title, prompt)
    return dialog.get_result()

class VoiceEnabledDialog(Toplevel):
    """
    A separate dialog used for typed/spoken input in certain refine flows.
    If you only use the main window’s "Speak" button, you might not use this at all.
    """
    def __init__(self, parent, title, prompt, is_multiline=False):
        super().__init__(parent)
        self.title(title)
        self.prompt = prompt
        self.result = None
        self.is_multiline = is_multiline
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        self.recognized_text = ""
        self.listening_thread = None

        if self.is_multiline:
            self.center_dialog(600, 300)
        else:
            self.center_dialog(600, 150)

        self.transient(parent)
        self.grab_set()

        self.label = tk.Label(self, text=self.prompt, wraplength=580)
        self.label.pack(pady=5)

        if self.is_multiline:
            self.input_widget = tk.Text(self, width=70, height=8)
        else:
            self.input_widget = tk.Entry(self, width=70)
        self.input_widget.pack(pady=5)

        self.button_frame = tk.Frame(self)
        self.button_frame.pack(pady=5)
        self.submit_button = tk.Button(self.button_frame, text="SUBMIT", width=10, command=self.on_submit)
        self.submit_button.pack(side=tk.LEFT, padx=5)
        self.speak_button = tk.Button(self.button_frame, text="Speak", width=10, command=self.on_speak)
        self.speak_button.pack(side=tk.LEFT, padx=5)
        self.done_button = tk.Button(self.button_frame, text="Done", width=10, command=self.on_done, state="disabled")
        self.done_button.pack(side=tk.LEFT, padx=5)
        self.cancel_button = tk.Button(self.button_frame, text="Cancel", width=10, command=self.on_cancel, state="disabled")
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        self.confirm_label = tk.Label(self.button_frame, text="")
        self.confirm_label.pack(side=tk.LEFT, padx=5)

        self.bind("<Return>", self.on_submit)
        self.input_widget.focus_set()

    def center_dialog(self, width, height):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def on_speak(self):
        if self.is_listening:
            return
        self.is_listening = True
        self.speak_button.config(state="disabled")
        self.submit_button.config(state="disabled")
        self.done_button.config(state="normal")
        self.cancel_button.config(state="normal")
        self.confirm_label.config(text="Listening...")
        self.recognized_text = ""
        self.listening_thread = threading.Thread(target=self.process_voice_input)
        self.listening_thread.start()

    def process_voice_input(self):
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            while self.is_listening:
                try:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    text = self.recognizer.recognize_google(audio)
                    self.recognized_text += " " + text
                    self.after(0, self.update_input_text, self.recognized_text.strip())
                except sr.UnknownValueError:
                    continue
                except sr.RequestError:
                    self.after(0, self.show_voice_error, "Error connecting to the speech recognition service.")
                    break
                except sr.WaitTimeoutError:
                    continue

    def update_input_text(self, text):
        if self.is_multiline:
            self.input_widget.delete("1.0", tk.END)
            self.input_widget.insert(tk.END, text)
        else:
            self.input_widget.delete(0, tk.END)
            self.input_widget.insert(0, text)

    def show_voice_error(self, message):
        tk.messagebox.showerror("Voice Error", message, parent=self)
        self.is_listening = False
        self.speak_button.config(state="normal")
        self.submit_button.config(state="normal")
        self.done_button.config(state="disabled")
        self.cancel_button.config(state="disabled")
        self.confirm_label.config(text="")

    def on_done(self):
        self.is_listening = False
        self.speak_button.config(state="normal")
        self.submit_button.config(state="normal")
        self.done_button.config(state="disabled")
        self.cancel_button.config(state="disabled")
        self.confirm_label.config(text="")
        if self.is_multiline:
            self.input_widget.delete("1.0", tk.END)
            self.input_widget.insert(tk.END, "Is this correct?")
        else:
            self.input_widget.delete(0, tk.END)
            self.input_widget.insert(0, "Is this correct?")
        parent_app = self.master
        while parent_app.master:
            parent_app = parent_app.master
        for child in parent_app.children.values():
            if hasattr(child, "set_output_text"):
                child.set_output_text("\nIs this correct?\n", replace=False)
                break

    def on_cancel(self):
        self.is_listening = False
        self.speak_button.config(state="normal")
        self.submit_button.config(state="normal")
        self.done_button.config(state="disabled")
        self.cancel_button.config(state="disabled")
        self.confirm_label.config(text="")
        self.input_widget.delete(0, tk.END) if not self.is_multiline else self.input_widget.delete("1.0", tk.END)

    def on_submit(self, event=None):
        if self.is_multiline:
            self.result = self.input_widget.get("1.0", tk.END).strip()
        else:
            self.result = self.input_widget.get().strip()
        self.destroy()

    def get_result(self):
        self.wait_window()
        return self.result

def voice_ask_string(title, prompt, parent, is_multiline=False):
    dialog = VoiceEnabledDialog(parent, title, prompt, is_multiline)
    return dialog.get_result()

class PropertySearchGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Property Search Assistant")
        self.center_window(650, 500)
        self.all_results = []
        self.current_query = ""
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        self.recognized_text = ""  # For concatenating voice input
        self.listening_thread = None

        self.instruction_label = tk.Label(master, text="Enter or speak your property search request:", font=("Arial", 12))
        self.instruction_label.pack(pady=5)

        self.input_text = tk.Text(master, height=4, width=80)
        self.input_text.pack(pady=5)

        self.guidance_label = tk.Label(master, text="Edit query or click 'Submit' to confirm.", font=("Arial", 8), fg="gray")
        self.guidance_label.pack(pady=2)

        self.button_frame = tk.Frame(master)
        self.button_frame.pack(pady=5)

        self.submit_button = tk.Button(self.button_frame, text="Submit", command=self.on_submit)
        self.submit_button.pack(side=tk.LEFT, padx=5)

        self.speak_button = tk.Button(self.button_frame, text="Speak", command=self.on_speak)
        self.speak_button.pack(side=tk.LEFT, padx=5)

        self.done_button = tk.Button(self.button_frame, text="Done", command=self.on_done, state="disabled")
        self.done_button.pack(side=tk.LEFT, padx=5)

        self.cancel_button = tk.Button(self.button_frame, text="Cancel", command=self.on_cancel, state="disabled")
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        self.confirm_label = tk.Label(self.button_frame, text="")
        self.confirm_label.pack(side=tk.LEFT, padx=5)

        self.output_area = ScrolledText(master, height=20, width=80)
        self.output_area.pack(pady=5)
        self.output_area.config(state="disabled")

        self.copy_button = tk.Button(master, text="Copy to Clipboard", command=self.copy_to_clipboard)
        self.copy_button.pack(pady=2)

    def center_window(self, width, height):
        self.master.update_idletasks()
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.master.geometry(f"{width}x{height}+{x}+{y}")

    def set_output_text(self, text, replace=True):
        self.output_area.config(state="normal")
        if replace:
            self.output_area.delete("1.0", tk.END)
        self.output_area.insert(tk.END, text)
        self.output_area.config(state="disabled")

    def copy_to_clipboard(self):
        self.output_area.config(state="normal")
        content = self.output_area.get("1.0", tk.END).strip()
        self.master.clipboard_clear()
        self.master.clipboard_append(content)
        self.output_area.config(state="disabled")
        messagebox.showinfo("Copied", "Text copied to clipboard!")

    def on_speak(self):
        """User pressed the Speak button in the main window."""
        if self.is_listening:
            return
        self.is_listening = True
        self.speak_button.config(state="disabled")
        self.submit_button.config(state="disabled")
        self.done_button.config(state="normal")
        self.cancel_button.config(state="normal")
        self.confirm_label.config(text="Listening...")
        self.set_output_text("Listening... Please speak your query.\n")
        self.recognized_text = ""  # Reset recognized text
        self.listening_thread = threading.Thread(target=self.process_voice_input)
        self.listening_thread.start()

    def process_voice_input(self):
        """Continuous listening in the main window's approach."""
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            while self.is_listening:
                try:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    text = self.recognizer.recognize_google(audio)
                    self.recognized_text += " " + text  # Concatenate recognized text
                    self.master.after(0, self.update_input_text, self.recognized_text.strip())
                except sr.UnknownValueError:
                    continue
                except sr.RequestError:
                    self.master.after(0, self.show_voice_error, "Error connecting to the speech recognition service.")
                    break
                except sr.WaitTimeoutError:
                    continue

    def update_input_text(self, text):
        """Updates the main text box with recognized text."""
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert(tk.END, text)
        self.set_output_text(f"Recognized: {text}\n", replace=True)

    def show_voice_error(self, message):
        self.is_listening = False
        self.speak_button.config(state="normal")
        self.submit_button.config(state="normal")
        self.done_button.config(state="disabled")
        self.cancel_button.config(state="disabled")
        self.confirm_label.config(text="")
        self.set_output_text(f"Error: {message}\n", replace=True)

    def on_done(self):
        """
        The user clicked Done after finishing a voice request in the main window.
        """
        self.is_listening = False
        self.speak_button.config(state="normal")
        self.submit_button.config(state="normal")
        self.done_button.config(state="disabled")
        self.cancel_button.config(state="disabled")
        self.confirm_label.config(text="")
        self.set_output_text("\nIs this correct?\n", replace=False)

    def on_cancel(self):
        self.is_listening = False
        self.speak_button.config(state="normal")
        self.submit_button.config(state="normal")
        self.done_button.config(state="disabled")
        self.cancel_button.config(state="disabled")
        self.confirm_label.config(text="")
        self.input_text.delete("1.0", tk.END)
        self.set_output_text("", replace=True)

    def on_submit(self):
        """When user clicks Submit (final)."""
        user_input = self.input_text.get("1.0", tk.END).strip()
        if not user_input or user_input == "Is this correct?":
            messagebox.showwarning("Input Error", "Please edit the query or type 'Yes' to confirm before submitting.")
            return
        self.current_query = user_input
        self.submit_button.config(state="disabled")
        self.speak_button.config(state="disabled")
        self.done_button.config(state="disabled")
        self.cancel_button.config(state="disabled")
        self.confirm_label.config(text="")
        self.set_output_text("Processing, please wait...\n", replace=True)

        thread = threading.Thread(target=self.run_query, args=(self.current_query,))
        thread.start()

    def run_query(self, user_input):
        """Calls process_user_input, then calls update_output with the results."""
        results = []
        try:
            result = process_user_input(data_list, user_input)
            if result:
                results.append(result)
        except Exception as e:
            self.master.after(0, self.set_output_text, f"Unexpected error: {str(e)}\n", True)
        self.master.after(0, self.update_output, results)

    def update_output(self, result):
        """Called after we get the parse result from GPT."""
        self.submit_button.config(state="normal")
        self.speak_button.config(state="normal")
        self.done_button.config(state="disabled")
        self.cancel_button.config(state="disabled")
        self.confirm_label.config(text="")

        if result:
            formatted_result = json.dumps(result, indent=4)
            self.set_output_text(formatted_result, replace=True)
            self.all_results.append(result)
        else:
            self.set_output_text("Error processing the query. Check console for details.", replace=True)
        
        self.followup_loop()

    def followup_loop(self):
        """Ask if user wants to refine. If yes, do add/new."""
        should_refine = ask_yes_no(self.master, "Refine Query", "Would you like to refine your search?")
        if not should_refine:
            self.input_text.delete("1.0", tk.END)
            return

        add_or_new = ask_add_new(self.master, "Query Option", "Add to current query or start new?")
        if add_or_new == "add":
            refinement = voice_ask_string("Add Refinement", "What would you like to add to your current query?", self.master, is_multiline=True)
            if refinement:
                self.current_query = self.current_query + " " + refinement
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert(tk.END, self.current_query)
                self.on_submit()
            else:
                self.input_text.delete("1.0", tk.END)
        elif add_or_new == "new":
            self.current_query = ""
            self.input_text.delete("1.0", tk.END)
            self.set_output_text("", replace=True)
        else:
            tk.messagebox.showinfo("Info", "No recognized option. Keeping current state.")

    def save_responses(self):
        """Save all collected results to JSON."""
        try:
            with open("all_responses.json", "w") as f:
                json.dump(self.all_results, f, indent=4)
            self.set_output_text("\nAll responses saved to all_responses.json.", replace=False)
        except Exception as e:
            self.set_output_text(f"\nError saving responses: {str(e)}", replace=False)

def load_excel_as_dicts(filename, sheet="Sheet1"):
    df = pd.read_excel(filename, sheet_name=sheet)
    required_columns = ["filter_category", "filter_name", "table_name", "column_name", "search_type"]
    df = df.dropna(subset=required_columns)
    row_dicts = []
    for _, row in df.iterrows():
        row_dict = {
            "filter_category": None if pd.isna(row["filter_category"]) else row["filter_category"],
            "filter_name": None if pd.isna(row["filter_name"]) else row["filter_name"],
            "table_name": None if pd.isna(row["table_name"]) else row["table_name"],
            "column_name": None if pd.isna(row["column_name"]) else row["column_name"],
            "column_value": None if pd.isna(row.get("column_value", None)) else row.get("column_value", None),
            "field_name": None if pd.isna(row.get("field_name", None)) else row.get("field_name", None),
            "search_type": None if pd.isna(row["search_type"]) else row["search_type"]
        }
        row_dicts.append(row_dict)
    return row_dicts

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
data_list = load_excel_as_dicts("filter_data.xlsx")

def process_user_input(data, user_input):
    parsed_data = parse_request_with_openai(data, user_input)
    if not parsed_data:
        print("\nError: Could not process user request.")
        return None

    print(json.dumps(parsed_data, indent=2))
    return parsed_data

def parse_request_with_openai(data, request):
    context_text = json.dumps(data, indent=2)
    prompt = f"""
Here is a dataset represented as a list of dictionaries:
{context_text}

From the following user request, please perform the following tasks:
1. Extract all city names mentioned in the request.
2. "filter_name": extract the filter name from the user query.
3. "values": the numeric range (e.g., [min, max]) or single value extracted (e.g., [value]).
4. Search the dataset to find the row that most closely matches the extracted filter name.

IMPORTANT:
- filter_category, filter_name, table_name, column_name, column_value, field_name should match the row exactly.
- If the row's search_type is 'min_max', handle numeric min/max. Use null if no lower or upper bound is mentioned.
- If the row's search_type is "Yes/No", set 'value' to 'True' for yes and 'False' for no
- If the row's search_type is NOT 'min_max', set 'search_type' to null in the final JSON (DO NOT keep the row's original search_type).
- If the user references something relevant (like 'University of Texas'), place it in 'value'.

NOTE ABOUT MULTIPLE FILTERS:
- If the user request contains multiple constraints (e.g., "at least 500 units and 1000 sqft"),
  return multiple objects in the "filters" array—one object per constraint.

If there are no constraints, just return the city with an empty "filters" array.

Return a JSON object with the following structure (valid JSON only):

{{
  "city": [ ... ],
  "filters": [
    {{
      "filter_category": "...",
      "filter_name": "...",
      "table_name": "...",
      "column_name": "...",
      "column_value": "...",
      "field_name": "...",
      "search_type": "...",
      "value": [...]
    }}
  ]
}}

User Request: "{request}"
""".strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

def open_file(filepath):
    if platform.system() == 'Darwin':
        subprocess.call(('open', filepath))
    elif platform.system() == 'Windows':
        os.startfile(filepath)
    else:
        subprocess.call(('xdg-open', filepath))

def on_closing(root, app):
    app.save_responses()
    if os.path.exists("all_responses.json"):
        open_file("all_responses.json")
    root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PropertySearchGUI(root)
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root, app))
    root.mainloop()