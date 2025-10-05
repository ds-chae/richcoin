# click_then_paste_cursor.py
import ctypes
from ctypes import wintypes
import psutil, time, sys, re
import uiautomation as auto
import pyperclip

# ====== Config ======
TEXT_TO_PASTE = "This should paste into the chat input, not the code editor. ✅"
CURSOR_EXE_HINTS = ("cursor.exe", "cursor-insiders.exe", "code.exe", "code-insiders.exe", "electron.exe")
PATH_SUBSTR_HINTS = (r"\\cursor\\",)
PLACEHOLDER_HINTS = (
    "plan, search, build anything",
    "plan, search, build",
    #"ask cursor",
    #"message",
    #"chat",
    #"input",
    #"prompt"
)
AUTOMATIONID_HINTS = ("chat", "input", "prompt", "textbox", "message", "composer")
MAX_DEPTH = 25
DEBUG = False  # set False when stable
# =====================

# --- Win32 bindings ---
user32 = ctypes.WinDLL('user32', use_last_error=True)
dwmapi = ctypes.WinDLL('dwmapi', use_last_error=True)
EnumWindows = user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
IsWindowVisible = user32.IsWindowVisible
GetWindowTextW = user32.GetWindowTextW
GetWindowTextLengthW = user32.GetWindowTextLengthW
GetClassNameW = user32.GetClassNameW
GetWindowThreadProcessId = user32.GetWindowThreadProcessId
SetForegroundWindow = user32.SetForegroundWindow
ShowWindow = user32.ShowWindow
SW_RESTORE = 9
DWMWA_CLOAKED = 14
DwmGetWindowAttribute = dwmapi.DwmGetWindowAttribute

import mouse

def fast_mouse_lib_click(x, y):
    """Moves the mouse and clicks using the 'mouse' library."""
    # Move immediately (duration=0) and click
    mouse.move(x, y, absolute=True, duration=0)
    mouse.click('left')


def is_cloaked(hwnd):
    cloaked = wintypes.DWORD()
    res = DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, ctypes.byref(cloaked), ctypes.sizeof(cloaked))
    return (res == 0) and (cloaked.value != 0)

def get_title(hwnd):
    n = GetWindowTextLengthW(hwnd)
    if n <= 0: return ""
    buf = ctypes.create_unicode_buffer(n + 1)
    GetWindowTextW(hwnd, buf, n + 1)
    return buf.value

def get_class(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    GetClassNameW(hwnd, buf, 256)
    return buf.value

def hwnd_pid(hwnd):
    pid = wintypes.DWORD()
    GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value

def exe_info(pid):
    try:
        p = psutil.Process(pid)
        return (p.exe() or "").lower(), (p.name() or "").lower(), " ".join(p.cmdline()).lower()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return "", "", ""

def list_visible_top_windows():
    out = []
    def _cb(hwnd, _):
        try:
            if not IsWindowVisible(hwnd) or is_cloaked(hwnd): return True
            pid = hwnd_pid(hwnd)
            exe_path, exe_name, cmdline = exe_info(pid)
            out.append({
                "hwnd": hwnd, "pid": pid,
                "title": get_title(hwnd), "class": get_class(hwnd),
                "exe_name": exe_name, "exe_path": exe_path, "cmdline": cmdline
            })
        except: pass
        return True
    EnumWindows(EnumWindowsProc(_cb), 0)
    return out

def pick_cursor_window(wins):
    # exe exact + cursor path/cmdline
    for w in wins:
        if w["exe_name"] in CURSOR_EXE_HINTS and (any(s in w["exe_path"] for s in PATH_SUBSTR_HINTS) or "cursor" in w["cmdline"]):
            return w
    # exe in hints + cursor in path/cmdline
    for w in wins:
        if any(h in w["exe_name"] for h in CURSOR_EXE_HINTS) and ("cursor" in w["exe_path"] or "cursor" in w["cmdline"]):
            return w
    # path mentions cursor
    for w in wins:
        if any(s in w["exe_path"] for s in PATH_SUBSTR_HINTS):
            return w
    # title fallback
    for w in wins:
        if re.search(r"cursor", (w["title"] or ""), re.I):
            return w
    return None

def bring_to_front(hwnd):
    try: ShowWindow(hwnd, SW_RESTORE); SetForegroundWindow(hwnd)
    except: pass

def rect_of(ctrl):
    try:
        r = ctrl.BoundingRectangle
        return (r.left, r.top, r.right, r.bottom, r.width(), r.height())
    except: return (0,0,0,0,0,0)

def control_bounds_ok(c):
    try:
        r = c.BoundingRectangle
        return (not c.IsOffscreen) and c.IsEnabled and r and r.width() > 0 and r.height() > 0
    except: return False

def iter_descendants(root, max_depth=25):
    def walk(node, depth):
        if depth > max_depth or node is None: return
        try: child = node.GetFirstChildControl()
        except: child = None
        while child:
            yield child
            yield from walk(child, depth+1)
            try: child = child.GetNextSiblingControl()
            except: break
    yield from walk(root, 0)

def L(s):  # lower/strip helper
    try: return (s or "").strip().lower()
    except: return ""

def score_chat_input(c):
    name, aid = L(getattr(c,"Name",None)), L(getattr(c,"AutomationId",None))
    lct, ctn = L(getattr(c,"LocalizedControlType",None)), L(getattr(c,"ControlTypeName",None))
    try: helptext = L(c.HelpText)
    except: helptext = ""
    left, top, right, bottom, w, h = rect_of(c)
    score = 0.0
    combo = " ".join(filter(None,(name,aid,helptext,lct,ctn)))
    if any(h in combo for h in PLACEHOLDER_HINTS): score += 100
    if any(h in aid for h in AUTOMATIONID_HINTS): score += 40
    if ctn == "editcontrol": score += 10
    if h>0:
        score += 10 if h<=80 else -5
    score += top*0.001  # prefer bottom-ish
    return score

import time

def print_elapsed_time(in_func, start_time):
    # 2. Record the END time
    end_time = time.time()

    # 3. Calculate the elapsed time
    elapsed_seconds = end_time - start_time

    # 4. Print the result
    print(f"{in_func} Elapsed Time: {elapsed_seconds:.4f} seconds")


def find_chat_input(uia_win, timeout=8.0, max_depth=MAX_DEPTH):
    deadline = time.time()+timeout
    while time.time() < deadline:
        edits = []
        for c in iter_descendants(uia_win, max_depth=max_depth):
            try:
                if control_bounds_ok(c) and c.ControlTypeName == "EditControl":
                    edits.append(c)
            except: pass

        if DEBUG:
            print("\n[DEBUG] Edit candidates:")
            for c in edits:
                name, aid = L(getattr(c,"Name",None)), L(getattr(c,"AutomationId",None))
                left, top, right, bottom, w, h = rect_of(c)
                print(f"  - name='{name}' aid='{aid}' rect=({left},{top},{w}x{h})")

        # exact placeholder first
        for c in edits:
            combo = " ".join([L(getattr(c,"Name",None)),
                              L(getattr(c,"AutomationId",None)),
                              L(getattr(c,"LocalizedControlType",None)),
                              L(getattr(c,"HelpText",None))])
            if any(h in combo for h in PLACEHOLDER_HINTS):
                return c

        #if edits:
        #    return max(edits, key=score_chat_input)
        maxc = None
        mleft = 0
        mtop = 0
        for c in edits:
            name, aid = L(getattr(c, "Name", None)), L(getattr(c, "AutomationId", None))
            left, top, right, bottom, w, h = rect_of(c)
            if left > mleft and top > mtop :
                maxc = c
        if maxc:
            return maxc

        time.sleep(0.01)
    return None

def click_center(c):
    start_time = time.time()
    # Try control.Click(); if it fails, click center via screen coords

    left, top, right, bottom, w, h = rect_of(c)
    if w>0 and h>0:
        x = int(left + w/2)
        y = int(top + h/2)
        try:
            fast_mouse_lib_click(x, y)
            #auto.Click(x, y)  # python-uiautomation global click
            print_elapsed_time('auto.Click()', start_time)
            return True
        except:
            # Very last resort: SetCursorPos + mouse_event
            SetCursorPos = user32.SetCursorPos
            mouse_event = user32.mouse_event
            MOUSEEVENTF_LEFTDOWN = 0x0002
            MOUSEEVENTF_LEFTUP   = 0x0004
            if SetCursorPos(x, y):
                mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                print_elapsed_time('mouse_event()', start_time)
                return True
    return False


# Paste
def paste_via_ctrl_v():
    ctrl_v()
    #auto.SendKeys("{Ctrl}v")

wins = None

def find_and_paste(text_to_paste):
    start_time = time.time()
    global wins
    if not None:
        wins = list_visible_top_windows()
    if DEBUG:
        print("Top-level visible windows:")
        for w in wins:
            print(f"HWND=0x{w['hwnd']:X} PID={w['pid']:<6} EXE={w['exe_name']:<20} "
                  f"Class={w['class']:<20} Title={(w['title'] or '')[:70]}")

    # 3) Put text on clipboard
    pyperclip.copy(text_to_paste)
    time.sleep(0.2)

    start_time = time.time()
    pick = pick_cursor_window(wins)
    print_elapsed_time('pick_cursor_window()', start_time)
    if not pick:
        print("ERROR: Cursor window not found. Adjust CURSOR_EXE_HINTS / PATH_SUBSTR_HINTS.", file=sys.stderr)
        sys.exit(1)

    print(f"\nPicked HWND=0x{pick['hwnd']:X} PID={pick['pid']} EXE={pick['exe_name']} Title='{pick['title']}'")
    bring_to_front(pick["hwnd"])

    start_time = time.time()
    try:
        uia_win = auto.ControlFromHandle(pick["hwnd"])
    except Exception:
        print("ERROR: UIA bind failed.", file=sys.stderr)
        sys.exit(2)

    chat = find_chat_input(uia_win, timeout=8.0, max_depth=MAX_DEPTH)
    if not chat:
        print("ERROR: Chat input not found. Make sure the chat panel is open/visible.", file=sys.stderr)
        sys.exit(3)

    start_time = time.time()
    # 1) Click the input box to move caret there
    if not click_center(chat):
        print("ERROR: Unable to click chat input.", file=sys.stderr)
        sys.exit(4)
    print_elapsed_time('click_center()', start_time)
    time.sleep(0.2)

    start_time = time.time()
    # 2) Navigate with arrow keys before pasting
    print("Navigating with arrow keys...")
    # Send 3 down arrow keys
    for i in range(13):
        st1 = time.time()
        tap(VK_DOWN, extended=True)
        #auto.SendKeys("{Down}")
        time.sleep(0.01)

    # Send 10 right arrow keys
    for i in range(50):
        st1 = time.time()
        #auto.SendKeys("{Right}")
        tap(VK_RIGHT, extended=True)
        time.sleep(0.01)
    
    print("Arrow key navigation completed")

    start_time = time.time()

    # 4) Send Ctrl+V keystroke
    paste_via_ctrl_v()

    print("Done: clicked input and sent Ctrl+V.")

    return True


# send_keys_fast.py
import time
import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)

# --- Win32 constants ---
INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP       = 0x0002
KEYEVENTF_SCANCODE    = 0x0008

# Virtual-key codes
VK_DOWN    = 0x28
VK_RIGHT   = 0x27
VK_CONTROL = 0x11
VK_V       = 0x56

MAPVK_VK_TO_VSC = 0

# --- Structures (correct definitions) ---
ULONG_PTR = wintypes.WPARAM  # pointer-sized
class KEYBDINPUT(ctypes.Structure):
    _fields_ = (("wVk",      wintypes.WORD),
                ("wScan",    wintypes.WORD),
                ("dwFlags",  wintypes.DWORD),
                ("time",     wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR))

class MOUSEINPUT(ctypes.Structure):
    _fields_ = (("dx",        wintypes.LONG),
                ("dy",        wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags",   wintypes.DWORD),
                ("time",      wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR))

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (("uMsg",    wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD))

class _INPUTUNION(ctypes.Union):
    _fields_ = (("ki", KEYBDINPUT),
                ("mi", MOUSEINPUT),
                ("hi", HARDWAREINPUT))

class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = (("type", wintypes.DWORD),
                ("u", _INPUTUNION))

SendInput = user32.SendInput
MapVirtualKey = user32.MapVirtualKeyW

def scancode(vk: int) -> int:
    return MapVirtualKey(vk, MAPVK_VK_TO_VSC)

def make_key_event(vk: int, keyup: bool = False, extended: bool = False) -> INPUT:
    flags = KEYEVENTF_SCANCODE
    if keyup:
        flags |= KEYEVENTF_KEYUP
    if extended:
        flags |= KEYEVENTF_EXTENDEDKEY
    return INPUT(type=INPUT_KEYBOARD,
                 ki=KEYBDINPUT(wVk=0,                 # 0 when using SCANCODE
                               wScan=scancode(vk),
                               dwFlags=flags,
                               time=0,
                               dwExtraInfo=0))

def send_inputs(events: list[INPUT]) -> None:
    n = len(events)
    arr = (INPUT * n)(*events)
    sent = SendInput(n, arr, ctypes.sizeof(INPUT))
    if sent != n:
        err = ctypes.get_last_error()
        raise OSError(f"SendInput sent {sent}/{n} events (GetLastError={err})")

def tap(vk: int, extended: bool = False):
    send_inputs([make_key_event(vk, False, extended),
                 make_key_event(vk, True,  extended)])

def ctrl_v():
    send_inputs([
        make_key_event(VK_CONTROL, False, False),
        make_key_event(VK_V,       False, False),
        make_key_event(VK_V,        True, False),
        make_key_event(VK_CONTROL,  True, False),
    ])

def down_right_paste():
    # Give yourself a moment to focus the target window
    time.sleep(0.6)

    # Arrow keys are EXTENDED keys → extended=True
    tap(VK_DOWN,  extended=True)
    tap(VK_RIGHT, extended=True)

    # Paste
    ctrl_v()

if __name__ == "__main__":
    find_and_paste(TEXT_TO_PASTE)
