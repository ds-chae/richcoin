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
    "ask cursor", "message", "chat", "input", "prompt"
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

        if edits:
            return max(edits, key=score_chat_input)

        time.sleep(0.01)
    return None

def click_center(c):
    # Try control.Click(); if it fails, click center via screen coords
    try:
        c.Click()
        return True
    except:
        pass
    left, top, right, bottom, w, h = rect_of(c)
    if w>0 and h>0:
        x = int(left + w/2)
        y = int(top + h/2)
        try:
            auto.Click(x, y)  # python-uiautomation global click
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
                return True
    return False

def paste_via_ctrl_v():
    auto.SendKeys("{Ctrl}v")

wins = None

def find_and_paste(text_to_paste):
    global wins
    if not None:
        wins = list_visible_top_windows()
    if DEBUG:
        print("Top-level visible windows:")
        for w in wins:
            print(f"HWND=0x{w['hwnd']:X} PID={w['pid']:<6} EXE={w['exe_name']:<20} "
                  f"Class={w['class']:<20} Title={(w['title'] or '')[:70]}")

    pick = pick_cursor_window(wins)
    if not pick:
        print("ERROR: Cursor window not found. Adjust CURSOR_EXE_HINTS / PATH_SUBSTR_HINTS.", file=sys.stderr)
        sys.exit(1)

    print(f"\nPicked HWND=0x{pick['hwnd']:X} PID={pick['pid']} EXE={pick['exe_name']} Title='{pick['title']}'")
    bring_to_front(pick["hwnd"])

    try:
        uia_win = auto.ControlFromHandle(pick["hwnd"])
    except Exception:
        print("ERROR: UIA bind failed.", file=sys.stderr)
        sys.exit(2)

    chat = find_chat_input(uia_win, timeout=8.0, max_depth=MAX_DEPTH)
    if not chat:
        print("ERROR: Chat input not found. Make sure the chat panel is open/visible.", file=sys.stderr)
        sys.exit(3)

    # 1) Click the input box to move caret there
    if not click_center(chat):
        print("ERROR: Unable to click chat input.", file=sys.stderr)
        sys.exit(4)

    # 2) Navigate with arrow keys before pasting
    print("Navigating with arrow keys...")
    # Send 3 down arrow keys
    for i in range(3):
        auto.SendKeys("{Down}")
        time.sleep(0.05)
    
    # Send 10 right arrow keys
    for i in range(10):
        auto.SendKeys("{Right}")
        time.sleep(0.05)
    
    print("Arrow key navigation completed")

    # 3) Put text on clipboard
    pyperclip.copy(text_to_paste)
    time.sleep(0.1)

    # 4) Send Ctrl+V keystroke
    paste_via_ctrl_v()

    print("Done: clicked input and sent Ctrl+V.")
    return True


if __name__ == "__main__":
    find_and_paste(TEXT_TO_PASTE)
