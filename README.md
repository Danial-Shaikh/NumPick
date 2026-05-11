# NumPick

NumPick is a lightweight desktop tool that lets you select, edit, and calculate numbers from anywhere on your screen.

It works with tables, PDFs, documents, spreadsheets, web pages, and any other place where you can highlight and copy text.

## What it does

NumPick helps you quickly calculate numbers without manually typing them into a calculator.

You can:

- Add numbers
- Subtract numbers
- Multiply numbers
- Divide numbers
- Find the average
- Edit detected numbers before calculating
- Copy the final result to your clipboard

## How it works

1. Highlight numbers anywhere on your screen
2. Press `Ctrl + C`
3. Right-click anywhere
4. Choose an operation like Add, Subtract, Multiply, Divide, or Average
5. NumPick shows the detected numbers and the final result
6. Edit the numbers if needed
7. Copy the result

## Example

If you copy this:

```text
149.99
89.50
299.00
412.75
296.21
```

And choose **Add**, NumPick will return:

```text
1247.45
```

## Requirements

Install Python first:

```text
https://www.python.org/downloads/
```

Make sure to check:

```text
Add Python to PATH
```

Then install the required Python packages:

```bash
pip install pyperclip pynput
```

## How to run

Download or clone this repo, then run:

```bash
python numcalc.py
```

Or double-click:

```text
numcalc.py
```

A small badge will appear on your screen:

```text
🔢 NumPick ● Running
```

That means NumPick is active.

## How to close NumPick

Right-click the small NumPick badge and click:

```text
Quit NumPick
```

## Troubleshooting

| Problem | Fix |
|---|---|
| Double-clicking does nothing | Right-click `numcalc.py` → Open with → Python |
| `pip is not recognized` | Reinstall Python and make sure `Add Python to PATH` is checked |
| Right-click menu does not show | Make sure you highlighted the numbers and pressed `Ctrl + C` first |
| Numbers are not detected properly | Try copying the values again, or manually edit the numbers in the popup |

## Notes

NumPick does not visually scan your screen. It reads the text that you copy to your clipboard.

So the correct flow is:

```text
Highlight numbers → Ctrl + C → Right-click → Choose calculation
```

## License

This project is open-source and free to use.
