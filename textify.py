# Execute this to install python libraries
#pip install -r requirements.txt

# Run the script using
# python textify.py

import typer
import logging
import requests
import os
import tkinter as tk
from tkinter import filedialog
from rich.console import Console
from rich.progress import Progress

# Initialize CLI app and logger
app = typer.Typer()
console = Console()
logging.basicConfig(filename="textify.log", level=logging.INFO, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Omeife AI API placeholders (replace with actual API endpoints)
OMEIFE_API = "https://apis.omeife.ai/api/v1/"
OMEIFE_TRANSLATE_API = OMEIFE_API+"user/developer/translate"
OMEIFE_TTS_API = OMEIFE_API+"user/developer/text-to-speech"
#API_KEY = os.getenv("OMEIFE_API_KEY")


def open_file_dialog():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
    return file_path


def save_file_dialog():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                             filetypes=[("Text Files", "*.txt")])
    return file_path


def translate_text(text: str, language: str, API_KEY: str) -> str:
    """Send text to Omeife AI for translation."""
    if not API_KEY:
        console.print("[bold red]\nAPI key is missing. Please set OMEIFE_API_KEY as an environment variable.[/bold red]")
        return ""
    try:
        response = requests.post(OMEIFE_TRANSLATE_API, json={"text": text, "from":"english", "to": language},
                                 headers={"Authorization": f"Bearer {API_KEY}"})
        response.raise_for_status()
        data =  response.json()
        return data["data"]["translated_text"]
    except Exception as e:
        logging.error(f"Translation error: {e}")
        console.print("[bold red]\n Oops!. Failed to translate.[/bold red]")
        return


def text_to_speech(text: str, language: str, save_path: str, API_KEY: str):
    """Convert text to speech and save as MP3."""
    if not API_KEY:
        console.print("[bold red]\nAPI key is missing. Please set OMEIFE_API_KEY as an environment variable.[/bold red]")
        return
    try:
        response = requests.post(OMEIFE_TTS_API, json={"text": text, "language": language},
                                 headers={"Authorization": f"Bearer {API_KEY}"})
        response.raise_for_status()
        audio_data = response.json()
        audio_url = audio_data["data"]["audio_url"]

        try:
          audio_response = requests.get(audio_url)
          audio_response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

          with open(save_path, "wb") as audio_file:
            audio_file.write(audio_response.content)
          logging.info("Speech synthesis successful.")
          console.print("\n\nAudio downloaded successfully as", save_path)
        except requests.exceptions.RequestException as e:
          console.print("[bold red]Error downloading audio: Check Logs[/bold red]")
          logging.error(f"Speech synthesis error: {e}")
        except Exception as e:
          console.print("[bold red]An unexpected error occured. Check Logs[/bold red]")
          logging.error(f"Speech synthesis error: {e}")          

    except Exception as e:
          logging.error(f"Speech synthesis error: {e}")


@app.command()
def run():
    API_KEY = typer.prompt("Input API Key") 
    console.print("\n[bold cyan]Welcome to Textify![/bold cyan]", style="bold green")
    language = typer.prompt("Choose translation language (Hausa,)")
    
    console.print("\nSelect a .txt file to translate...")
    file_path = open_file_dialog()
    if not file_path:
        console.print("[bold red]No file selected. Exiting.[/bold red]")
        return
    
    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()
    
    console.print("[bold yellow]Translating...[/bold yellow]")
    with Progress() as progress:
        task = progress.add_task("Translating", total=100)
        translated_text = translate_text(text, language, API_KEY)
        progress.update(task, advance=100)
    
    console.print("\n[bold yellow]Translated from English to: [/bold yellow]", language)
    console.print("[bold green]Translation Complete:[/bold green]", translated_text, "\n")

    if typer.confirm("Do you want to save the translated text?"):
      save_path = save_file_dialog()
      if save_path:
          with open(save_path, "w", encoding="utf-8") as file:
              file.write(translated_text)
          console.print(f"[bold cyan]Translated file saved at: {save_path}\n[/bold cyan]")
    
    if typer.confirm("Do you want to convert the text to speech?"):
        speech_save_path = filedialog.asksaveasfilename(defaultextension=".wav",
                                                        filetypes=[("WAV Files", "*.wav")])
        if speech_save_path:
            console.print("[bold yellow]Generating speech...[/bold yellow]")
            with Progress() as progress:
                task = progress.add_task("Generating Speech", total=100)
                text_to_speech(translated_text, language, speech_save_path, API_KEY)
                progress.update(task, advance=100)
            console.print(f"[bold cyan]\nSpeech file saved at: {speech_save_path}[/bold cyan]")
    
    console.print("[bold green]Process Complete![/bold green]")

if __name__ == "__main__":
    app()
