import os, time
from datetime import date, datetime, timedelta

def log(message, type="INFO"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    line = f"[{timestamp}] [{type}]: {message}"
    print(line)
    os.makedirs("logs", exist_ok=True)
    with open(os.path.join("logs", f"{timestamp[:10]}.log"), "a", encoding="utf-8") as file:
        file.write(line + "\n")

def clearlogs():
    cutoff = date.today() - timedelta(days=7)
    removed_files = []
    for filename in os.listdir("logs"):
        file_path = os.path.join("logs", filename)
        if os.path.isfile(file_path) and filename.endswith(".log") and datetime.strptime(filename[:-4], "%Y-%m-%d").date() <= cutoff:
            os.remove(file_path)
            removed_files.append(filename)
    log(f"Old logs cleared: {', '.join(removed_files)}")
