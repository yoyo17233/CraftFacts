import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Example usage
install("discord.py")
install("google-genai")
install("python-dotenv")