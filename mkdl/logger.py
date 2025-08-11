COLOR = {
    "reset": "\033[0m", "bold": "\033[1m",
    "red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m", "cyan": "\033[36m"
}

def paint(code, s): 
    return f"{code}{s}{COLOR['reset']}"

paintGreen = lambda s: paint(COLOR['green'], s)
paintRed = lambda s: paint(COLOR['red'], s)
paintYellow = lambda s: paint(COLOR['yellow'], s)
paintCyan = lambda s: paint(COLOR['cyan'], s)

def logInfo(*a): print("ℹ️", *a)
def logSuccess(*a): print("✅", *a)
def logWarn(*a): print("⚠️", *a)
def logError(*a): print("❌", *a)
