import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
import requests
from bs4 import BeautifulSoup
import webbrowser

# Creiamo una sessione per gestire le richieste HTTP
session = requests.Session()

def get_xsrf_token(url):
    """Ottiene il token CSRF e i cookie dalla pagina."""
    response = session.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        token_input = soup.find("input", {"name": "_token"})
        if token_input:
            token_value = token_input["value"]
            cookies_get = session.cookies.get_dict()
            return token_value, response.url, cookies_get
    return None, None, None

def convert_and_upload_audio(input_file_path, post_url, creator, title, log_console):
    """Converte un MP3 in WAV e lo invia tramite una richiesta POST a FABA."""
    xsrf_token, new_url, cookie = get_xsrf_token(post_url)
    if not xsrf_token:
        log_console.log("Errore nel recupero del token.")
        return
    with open(input_file_path, "rb") as mp3file:
        files = {"userAudio": mp3file}
        data = {"_token": xsrf_token, "creator": creator, "title": title}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Referer": new_url
        }
        log_console.log("Attendere Caricamento sui Server FABA in corso....")
        response = session.post(new_url, data=data, headers=headers, files=files)

    if response.status_code == 200:
        log_console.log("File inviato con successo! Ora puoi sincronizzare dal tuo FABA o FABA+")
    else:
        log_console.log(f"Errore nell'invio: {response.status_code} - {response.text}")

class ConsoleLogger:
    """Classe che permette di reindirizzare le stampe (stdout) direttamente alla console della GUI."""
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def log(self, message):
        """Stampa un messaggio nella console della GUI."""
        self.text_widget.configure(state='normal')
        self.text_widget.insert(tk.END, message + "\n")
        self.text_widget.see(tk.END)
        self.text_widget.configure(state='disabled')

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Caricatore FABA ME Rosso - Compatibile con Faba e Faba+ ")
        self.geometry("800x600")  # Dimensioni maggiori per ospitare tutte le aree

        # Frame dei pulsanti principali
        frame_buttons = ttk.Frame(self)
        frame_buttons.pack(padx=10, pady=10, fill="x")

        ttk.Button(frame_buttons, text="Acquista FabaMe Red", command=self.acquista_fabame_red).grid(
            row=0, column=0, padx=5, pady=5, sticky="ew"
        )
        ttk.Button(frame_buttons, text="Acquista Faba+", command=self.acquista_fabame_red).grid(
            row=0, column=1, padx=5, pady=5, sticky="ew"
        )
        ttk.Button(frame_buttons, text="Acquista FabaMe Cubo", command=self.acquista_fabame_red).grid(
            row=0, column=2, padx=5, pady=5, sticky="ew"
        )
        ttk.Button(frame_buttons, text="Manuale di utilizzo", command=self.open_manual).grid(
            row=0, column=3, padx=5, pady=5, sticky="ew"
        )
        ttk.Button(frame_buttons, text="Supporto", command=self.open_support).grid(
            row=0, column=4, padx=5, pady=5, sticky="ew"
        )
        ttk.Button(frame_buttons, text="Comprami un caffe", command=self.compra_caffe).grid(
            row=0, column=5, padx=5, pady=5, sticky="ew"
        )

        # Riquadro per il caricamento audio direttamente nella finestra principale
        frame_upload = ttk.LabelFrame(self, text="Carica Audio su FABA ME Red")
        frame_upload.pack(padx=10, pady=10, fill="both", expand=True)

        # Campo per l'URL di destinazione
        ttk.Label(frame_upload, text="URL di invito a registrare:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.url_var = tk.StringVar()
        ttk.Entry(frame_upload, textvariable=self.url_var, width=60).grid(row=0, column=1, padx=5, pady=5)

        # Campo per la selezione del file MP3
        ttk.Label(frame_upload, text="Seleziona un file MP3:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.file_var = tk.StringVar()
        file_entry = ttk.Entry(frame_upload, textvariable=self.file_var, width=60, state="readonly")
        file_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(frame_upload, text="Sfoglia", command=self.select_file).grid(row=1, column=2, padx=5, pady=5)

        # Campo per il Nome Creatore
        ttk.Label(frame_upload, text="Nome Creatore:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.creator_var = tk.StringVar()
        ttk.Entry(frame_upload, textvariable=self.creator_var, width=60).grid(row=2, column=1, padx=5, pady=5)

        # Campo per il Titolo della Traccia
        ttk.Label(frame_upload, text="Titolo della Traccia:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.title_var = tk.StringVar()
        ttk.Entry(frame_upload, textvariable=self.title_var, width=60).grid(row=3, column=1, padx=5, pady=5)

        # Pulsante per avviare il caricamento
        ttk.Button(frame_upload, text="Carica Audio", command=self.upload_audio).grid(
            row=4, column=0, columnspan=3, pady=10
        )

        # Area di log (console)
        self.log_area = scrolledtext.ScrolledText(self, wrap='word', height=10, state='disabled')
        self.log_area.pack(padx=10, pady=10, fill="both", expand=True)

        # Logger per la console
        self.console_logger = ConsoleLogger(self.log_area)

        # Verifica della presenza della cartella ffmpeg
        current_dir_ffmpeg = os.getcwd()
        folder_name = "ffmpeg"
        folder_path_ffmpeg = os.path.join(current_dir_ffmpeg, folder_name)
        if os.path.exists(folder_path_ffmpeg) and os.path.isdir(folder_path_ffmpeg):
            self.ffmpeg_path = f"{folder_path_ffmpeg}{os.sep}bin"
            self.console_logger.log("Tutto OK avviato correttamente")
            os.environ['PATH'] += f';{self.ffmpeg_path}'
        else:
            self.console_logger.log("Errore: manca la cartella ffmpeg")

    def acquista_fabame_red(self):
        """Apre la pagina di acquisto di FabaMe Red."""
        webbrowser.open("https://amzn.to/4ihxENF")

    def acquista_fabame_cubo(self):
        """Apre la pagina di acquisto di FabaMe Red."""
        webbrowser.open("https://amzn.to/4bYe5Yc")

    def acquista_fabame_plus(self):
        """Apre la pagina di acquisto di FabaMe Red."""
        webbrowser.open("https://amzn.to/3Fv46xu")
    def open_manual(self):
        """Apre il manuale di utilizzo (PDF o pagina web)."""
        manual_path = f"{os.getcwd()}{os.sep}manuale.pdf"  # Sostituisci con il percorso del file PDF
        if os.path.exists(manual_path):
            os.startfile(manual_path)  # Windows
        else:
            webbrowser.open("https://www.myfaba.com/")  # Link di riferimento

    def open_support(self):
        """Apre la pagina di supporto."""
        webbrowser.open("https://www.facebook.com/messages/e2ee/t/9787101408002159")
    def compra_caffe(self):
        """Apre la pagina di supporto."""
        webbrowser.open("https://buymeacoffee.com/salcolantop")
    def select_file(self):
        """Apre il file dialog per selezionare un file MP3."""
        file_path = filedialog.askopenfilename(filetypes=[("MP3 Files", "*.mp3")])
        if file_path:
            self.file_var.set(file_path)

    def upload_audio(self):
        """Avvia il processo di conversione e caricamento in un thread separato."""
        url = self.url_var.get().strip()
        file_path = self.file_var.get().strip()
        creator = self.creator_var.get().strip()
        title = self.title_var.get().strip()

        # Verifica che l'URL contenga "https://studio.faba"
        if "https://studio" not in url:
            self.console_logger.log("Errore: L'URL non sembra un link di invito al Faba Me Rosso'")
            return

        if not url or not file_path or not creator or not title:
            self.console_logger.log("Errore: compila tutti i campi prima di procedere.")
            return

        self.console_logger.log(f"Inizio caricamento di {file_path} su {url}")
        threading.Thread(target=convert_and_upload_audio, args=(file_path, url, creator, title, self.console_logger), daemon=True).start()

if __name__ == "__main__":
    app = App()
    app.mainloop()
