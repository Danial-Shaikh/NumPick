"""
NumPick - Select numbers anywhere on screen, right-click to calculate.

Requirements:
pip install pyperclip pynput

Run:
python numcalc.py
"""

import tkinter as tk
import pyperclip
import re
import sys


# ─────────────────────────────────────────
#  Core: clean text + extract numbers
# ─────────────────────────────────────────

def normalize_text(text):
    """
    Cleans weird formatting copied from PDFs, Excel, Word, etc.
    Handles:
    - Unicode minus signs
    - Currency symbols
    - Commas in numbers
    - Spaces around decimals like 149. 99
    """
    if not text:
        return ""

    text = text.replace("−", "-")
    text = text.replace("–", "-")
    text = text.replace("—", "-")

    # Remove common currency symbols/text
    text = text.replace("$", "")
    text = text.replace("CAD", "")
    text = text.replace("USD", "")

    # Fix cases like 149. 99 or 149 .99 or 149 . 99
    text = re.sub(r'(\d)\s*\.\s*(\d)', r'\1.\2', text)

    # Remove commas inside numbers: 1,247.45 -> 1247.45
    text = re.sub(r'(?<=\d),(?=\d)', '', text)

    return text


def extract_numbers(text):
    """
    Pull every number from text.
    Supports:
    - integers
    - decimals
    - negatives
    - comma numbers
    - messy copied text
    """
    text = normalize_text(text)

    pattern = r'-?\d+(?:\.\d+)?'
    matches = re.findall(pattern, text)

    numbers = []
    for match in matches:
        try:
            numbers.append(float(match))
        except ValueError:
            pass

    return numbers


def should_show_numpick(text, min_numbers=3):
    """
    Decide whether NumPick should appear.

    NumPick will only show when copied text looks like a real group
    of numeric/table data.

    This prevents it from popping up when copying normal text,
    quote numbers, random IDs, sentences, etc.
    """
    if not text or not text.strip():
        return False

    numbers = extract_numbers(text)

    # Require at least a few numbers
    if len(numbers) < min_numbers:
        return False

    cleaned = normalize_text(text)

    # Count letters and digits
    letter_count = len(re.findall(r'[A-Za-z]', cleaned))
    digit_count = len(re.findall(r'\d', cleaned))

    # If there are way more letters than digits,
    # it is probably normal copied text, not numeric data.
    if digit_count == 0:
        return False

    if letter_count > digit_count * 2:
        return False

    # Strong signs that the copied data is from a table/spreadsheet/list
    has_table_formatting = (
        "\n" in cleaned or
        "\t" in cleaned or
        "$" in text or
        "," in text
    )

    # If there are 5+ numbers, it is very likely numeric data
    if len(numbers) >= 5:
        return True

    # If there are only 3-4 numbers, require table/list-like formatting
    if len(numbers) >= min_numbers and has_table_formatting:
        return True

    return False


def format_number(n):
    """Show clean number formatting."""
    if isinstance(n, float) and n == int(n):
        return str(int(n))
    return str(round(n, 8)).rstrip("0").rstrip(".")


def calculate_result(operation, numbers):
    if len(numbers) == 0:
        raise ValueError("No numbers found.")

    if len(numbers) < 2 and operation in ("Subtract", "Divide"):
        raise ValueError(f"Need at least 2 numbers to {operation.lower()}.")

    if operation == "Add":
        return sum(numbers)

    elif operation == "Subtract":
        result = numbers[0]
        for n in numbers[1:]:
            result -= n
        return result

    elif operation == "Multiply":
        result = 1
        for n in numbers:
            result *= n
        return result

    elif operation == "Divide":
        result = numbers[0]
        for n in numbers[1:]:
            if n == 0:
                raise ValueError("Cannot divide by zero.")
            result /= n
        return result

    elif operation == "Average":
        return sum(numbers) / len(numbers)

    else:
        raise ValueError("Invalid operation.")


# ─────────────────────────────────────────
#  Result popup window
# ─────────────────────────────────────────

class ResultPopup(tk.Toplevel):
    def __init__(self, master, operation, numbers):
        super().__init__(master)

        self.operation = operation
        self.numbers = numbers
        self.result_var = ""

        self.title("NumPick Result")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        # ── Styling ──
        self.BG = "#1a1a2e"
        self.CARD = "#16213e"
        self.ACCENT = "#e94560"
        self.TEXT = "#eaeaea"
        self.SUBTLE = "#8892a4"
        self.FONT = ("Segoe UI", 11)
        self.FONT_SM = ("Segoe UI", 9)
        self.MONO = ("Cascadia Code", 12) if self._font_exists("Cascadia Code") else ("Courier New", 12)

        self.configure(bg=self.BG)

        outer = tk.Frame(self, bg=self.BG, padx=24, pady=20)
        outer.pack(fill="both", expand=True)

        # Title row
        title_row = tk.Frame(outer, bg=self.BG)
        title_row.pack(fill="x", pady=(0, 14))

        tk.Label(
            title_row,
            text="●",
            fg=self.ACCENT,
            bg=self.BG,
            font=("Segoe UI", 9)
        ).pack(side="left")

        tk.Label(
            title_row,
            text=f"  {operation}",
            fg=self.TEXT,
            bg=self.BG,
            font=("Segoe UI", 11, "bold")
        ).pack(side="left")

        # Numbers detected label
        tk.Label(
            outer,
            text="Numbers detected/editable:",
            fg=self.SUBTLE,
            bg=self.BG,
            font=self.FONT_SM,
            anchor="w"
        ).pack(fill="x")

        # Editable numbers box
        self.numbers_text = tk.Text(
            outer,
            height=4,
            width=42,
            fg=self.TEXT,
            bg=self.CARD,
            insertbackground=self.ACCENT,
            font=self.MONO,
            relief="flat",
            padx=10,
            pady=8,
            wrap="word"
        )
        self.numbers_text.pack(fill="x", pady=(2, 8))

        nums_text = "  ".join(format_number(n) for n in numbers)
        self.numbers_text.insert("1.0", nums_text)

        # Helpful note
        tk.Label(
            outer,
            text="Tip: Edit/add/remove numbers above, then click Recalculate.",
            fg=self.SUBTLE,
            bg=self.BG,
            font=("Segoe UI", 8),
            anchor="w"
        ).pack(fill="x", pady=(0, 10))

        # Recalculate button
        tk.Button(
            outer,
            text="↻  Recalculate",
            command=self._recalculate,
            bg=self.CARD,
            fg=self.TEXT,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=6,
            cursor="hand2",
            activebackground="#0f3460",
            activeforeground=self.TEXT
        ).pack(anchor="w", pady=(0, 12))

        # Result label
        tk.Label(
            outer,
            text="Result:",
            fg=self.SUBTLE,
            bg=self.BG,
            font=self.FONT_SM,
            anchor="w"
        ).pack(fill="x")

        self.result_frame = tk.Frame(outer, bg=self.ACCENT, padx=2, pady=2)
        self.result_frame.pack(fill="x", pady=(2, 16))

        self.result_label = tk.Label(
            self.result_frame,
            text="",
            fg="#ffffff",
            bg=self.CARD,
            font=("Segoe UI", 18, "bold"),
            anchor="w",
            padx=12,
            pady=8
        )
        self.result_label.pack(fill="both")

        # Buttons
        btn_row = tk.Frame(outer, bg=self.BG)
        btn_row.pack(fill="x")

        copy_btn = tk.Button(
            btn_row,
            text="📋  Copy Result",
            command=self._copy,
            bg=self.ACCENT,
            fg="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=7,
            cursor="hand2",
            activebackground="#c73652",
            activeforeground="white"
        )
        copy_btn.pack(side="left", padx=(0, 8))

        close_btn = tk.Button(
            btn_row,
            text="Close",
            command=self.destroy,
            bg=self.CARD,
            fg=self.SUBTLE,
            relief="flat",
            font=("Segoe UI", 10),
            padx=14,
            pady=7,
            cursor="hand2",
            activebackground="#0f3460",
            activeforeground=self.TEXT
        )
        close_btn.pack(side="left")

        self._recalculate()
        self._center()

    def _recalculate(self):
        raw_text = self.numbers_text.get("1.0", "end")
        numbers = extract_numbers(raw_text)

        try:
            result = calculate_result(self.operation, numbers)
            self.numbers = numbers
            self.result_var = format_number(result)
            self.result_label.config(text=self.result_var, fg="#ffffff")
        except Exception as e:
            self.result_var = ""
            self.result_label.config(text=f"Error: {str(e)}", fg=self.ACCENT)

    def _copy(self):
        if self.result_var:
            pyperclip.copy(self.result_var)
            self.destroy()

    def _center(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    def _font_exists(self, name):
        try:
            import tkinter.font as tkfont
            return name in tkfont.families()
        except Exception:
            return False


# ─────────────────────────────────────────
#  Error popup
# ─────────────────────────────────────────

class ErrorPopup(tk.Toplevel):
    def __init__(self, master, message):
        super().__init__(master)

        self.title("NumPick")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.configure(bg="#1a1a2e")

        outer = tk.Frame(self, bg="#1a1a2e", padx=24, pady=18)
        outer.pack()

        tk.Label(
            outer,
            text="⚠️  " + message,
            fg="#e94560",
            bg="#1a1a2e",
            font=("Segoe UI", 11)
        ).pack()

        tk.Button(
            outer,
            text="OK",
            command=self.destroy,
            bg="#16213e",
            fg="#eaeaea",
            relief="flat",
            font=("Segoe UI", 10),
            padx=16,
            pady=6,
            cursor="hand2"
        ).pack(pady=(12, 0))

        self.after(100, self._center)

    def _center(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")


# ─────────────────────────────────────────
#  Right-click context menu
# ─────────────────────────────────────────

class CalcMenu(tk.Menu):
    OPERATIONS = [
        ("➕  Add", "Add"),
        ("➖  Subtract", "Subtract"),
        ("✖️  Multiply", "Multiply"),
        ("➗  Divide", "Divide"),
        ("〜  Average", "Average"),
    ]

    def __init__(self, master, text, x, y):
        super().__init__(
            master,
            tearoff=0,
            bg="#1a1a2e",
            fg="#eaeaea",
            activebackground="#e94560",
            activeforeground="white",
            font=("Segoe UI", 10),
            bd=0,
            relief="flat"
        )

        self.master_win = master
        self.text = text

        self.add_command(
            label="NumPick  🔢",
            state="disabled",
            font=("Segoe UI", 9, "bold")
        )
        self.add_separator()

        for label, op in self.OPERATIONS:
            self.add_command(
                label=label,
                command=lambda o=op: self._run(o)
            )

        self.add_separator()
        self.add_command(label="✖  Cancel", command=self.unpost)

        # Place NumPick beside the normal right-click menu area.
        # Increase offset_x if you want even more space.
        offset_x = 300
        offset_y = 10

        screen_w = master.winfo_screenwidth()
        screen_h = master.winfo_screenheight()

        menu_x = x + offset_x
        menu_y = y + offset_y

        # Keep menu inside screen bounds
        if menu_x > screen_w - 240:
            menu_x = x - 300

        if menu_y > screen_h - 260:
            menu_y = screen_h - 280

        if menu_y < 0:
            menu_y = 20

        try:
            self.tk_popup(menu_x, menu_y)
        finally:
            self.grab_release()

    def _run(self, operation):
        numbers = extract_numbers(self.text)

        if len(numbers) == 0:
            ErrorPopup(self.master_win, "No numbers found in your selection.")
            return

        try:
            calculate_result(operation, numbers)
            ResultPopup(self.master_win, operation, numbers)
        except Exception as e:
            ErrorPopup(self.master_win, str(e))


# ─────────────────────────────────────────
#  Main app
# ─────────────────────────────────────────

class NumPickApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NumPick")
        self.root.withdraw()

        self.root.iconify()
        self.root.protocol("WM_DELETE_WINDOW", self._quit)

        self._build_indicator()
        self._setup_hotkey()

        self.root.mainloop()

    def _build_indicator(self):
        self.indicator = tk.Toplevel(self.root)
        self.indicator.title("")
        self.indicator.geometry("160x36+20+20")
        self.indicator.attributes("-topmost", True)
        self.indicator.attributes("-alpha", 0.92)
        self.indicator.resizable(False, False)
        self.indicator.configure(bg="#1a1a2e")
        self.indicator.protocol("WM_DELETE_WINDOW", self._quit)

        tk.Label(
            self.indicator,
            text="🔢 NumPick  ●  Running",
            fg="#e94560",
            bg="#1a1a2e",
            font=("Segoe UI", 8, "bold"),
            padx=8
        ).pack(expand=True)

        self.indicator.bind("<Button-3>", lambda e: self._show_indicator_menu(e))

    def _show_indicator_menu(self, event):
        m = tk.Menu(
            self.root,
            tearoff=0,
            bg="#1a1a2e",
            fg="#eaeaea",
            activebackground="#e94560",
            activeforeground="white",
            font=("Segoe UI", 10)
        )

        m.add_command(label="Quit NumPick", command=self._quit)

        try:
            m.tk_popup(event.x_root, event.y_root)
        finally:
            m.grab_release()

    def _setup_hotkey(self):
        try:
            from pynput import mouse

            def on_click(x, y, button, pressed):
                if button == mouse.Button.right and not pressed:
                    try:
                        text = pyperclip.paste()
                    except Exception:
                        text = ""

                    # Only show NumPick when clipboard looks like numeric/table data.
                    # This stops it from popping up on normal copied text or quote numbers.
                    if should_show_numpick(text, min_numbers=3):
                        self.root.after(0, lambda: CalcMenu(self.root, text, x, y))
                    else:
                        return

            listener = mouse.Listener(on_click=on_click)
            listener.daemon = True
            listener.start()

        except ImportError:
            self._fallback_ui()

    def _fallback_ui(self):
        win = tk.Toplevel(self.root)
        win.title("NumPick — Paste Numbers")
        win.attributes("-topmost", True)
        win.configure(bg="#1a1a2e")
        win.geometry("400x300")

        outer = tk.Frame(win, bg="#1a1a2e", padx=20, pady=16)
        outer.pack(fill="both", expand=True)

        tk.Label(
            outer,
            text="Paste your numbers below",
            fg="#eaeaea",
            bg="#1a1a2e",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w")

        tk.Label(
            outer,
            text="Copy numbers first, then paste/edit them here.",
            fg="#8892a4",
            bg="#1a1a2e",
            font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(2, 10))

        txt = tk.Text(
            outer,
            height=5,
            font=("Courier New", 11),
            bg="#16213e",
            fg="#eaeaea",
            insertbackground="#e94560",
            relief="flat",
            padx=8,
            pady=6
        )
        txt.pack(fill="x")

        btn_row = tk.Frame(outer, bg="#1a1a2e")
        btn_row.pack(pady=12, fill="x")

        for label, op in [
            ("Add", "Add"),
            ("Subtract", "Subtract"),
            ("Multiply", "Multiply"),
            ("Divide", "Divide"),
            ("Average", "Average")
        ]:
            tk.Button(
                btn_row,
                text=label,
                command=lambda o=op: ResultPopup(self.root, o, extract_numbers(txt.get("1.0", "end"))),
                bg="#e94560",
                fg="white",
                relief="flat",
                font=("Segoe UI", 9),
                padx=8,
                pady=4,
                cursor="hand2"
            ).pack(side="left", padx=2)

    def _quit(self):
        self.root.destroy()
        sys.exit(0)


# ─────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────

if __name__ == "__main__":
    NumPickApp()
