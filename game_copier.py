import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import shutil
import threading
import subprocess

class GameCopier:
    def __init__(self, root):
        self.root = root
        self.root.title("Copiador de Jogos")
        self.root.geometry("600x400")
        
        # Variáveis
        self.source_path = tk.StringVar()
        self.dest_path = tk.StringVar()
        self.total_size = 0
        self.copied_size = 0
        
        self.setup_ui()
        
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Origem
        ttk.Label(main_frame, text="Pasta de Origem:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(main_frame, textvariable=self.source_path, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(main_frame, text="Procurar", command=self.select_source).grid(row=0, column=2)
        
        # Destino
        ttk.Label(main_frame, text="Pasta de Destino:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(main_frame, textvariable=self.dest_path, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(main_frame, text="Procurar", command=self.select_dest).grid(row=1, column=2)
        
        # Barra de Progresso
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.grid(row=2, column=0, columnspan=3, pady=20)
        
        self.progress = ttk.Progressbar(self.progress_frame, length=400, mode='determinate')
        self.progress.grid(row=0, column=0, columnspan=3)
        
        self.progress_label = ttk.Label(self.progress_frame, text="0%")
        self.progress_label.grid(row=1, column=0, columnspan=3)
        
        # Status
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.grid(row=3, column=0, columnspan=3)
        
        # Botão Iniciar
        ttk.Button(main_frame, text="Iniciar Cópia", command=self.start_copy).grid(row=4, column=0, columnspan=3, pady=10)

    def run_rufus(self):
        rufus_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rufus.exe")
        if os.path.exists(rufus_path):
            try:
                subprocess.Popen([rufus_path])
                return True
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao executar Rufus: {str(e)}")
                return False
        else:
            messagebox.showerror("Erro", "Arquivo rufus.exe não encontrado na pasta do script!")
            return False

    def check_destination(self):
        dest = self.dest_path.get()
        if os.path.exists(dest) and os.listdir(dest):
            response = messagebox.askyesno(
                "Destino não vazio",
                "A pasta de destino contém arquivos/pastas. Deseja executar o Rufus para formatar o dispositivo?",
                icon='warning'
            )
            if response:
                return self.run_rufus()
            return False
        return True

    def select_source(self):
        path = filedialog.askdirectory()
        if path:
            self.source_path.set(path)
            
    def select_dest(self):
        path = filedialog.askdirectory()
        if path:
            self.dest_path.set(path)
            
    def get_folder_size(self, path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total_size += os.path.getsize(fp)
                except OSError:
                    continue
        return total_size

    def update_progress(self, copied_size):
        self.copied_size = copied_size
        if self.total_size > 0:
            percentage = (self.copied_size / self.total_size) * 100
            self.progress['value'] = percentage
            self.progress_label.config(text=f"{percentage:.1f}%")
            self.root.update_idletasks()

    def copy_with_progress(self, src, dst):
        if os.path.isdir(src):
            if not os.path.exists(dst):
                os.makedirs(dst)
            for item in os.listdir(src):
                s = os.path.join(src, item)
                d = os.path.join(dst, item)
                self.copy_with_progress(s, d)
        else:
            shutil.copy2(src, dst)
            self.update_progress(self.copied_size + os.path.getsize(src))
        
    def copy_files(self):
        source = self.source_path.get()
        dest = self.dest_path.get()
        
        try:
            # Verificar se o destino está vazio
            if not self.check_destination():
                self.status_label.config(text="Operação cancelada pelo usuário")
                return

            # Calcular tamanho total
            self.status_label.config(text="Calculando tamanho total...")
            self.total_size = self.get_folder_size(source)
            self.copied_size = 0
            
            if not os.path.exists(source) or not os.path.exists(dest):
                messagebox.showerror("Erro", "Pasta de origem ou destino inválida!")
                return
                
            # Verificar espaço disponível
            _, _, free_space = shutil.disk_usage(dest)
            if self.total_size > free_space:
                messagebox.showerror("Erro", "Espaço insuficiente no destino!")
                return
                
            # Copiar todas as pastas exceto DVD primeiro
            for item in os.listdir(source):
                if item != "DVD":
                    source_item = os.path.join(source, item)
                    dest_item = os.path.join(dest, item)
                    
                    self.status_label.config(text=f"Copiando: {item}")
                    self.copy_with_progress(source_item, dest_item)
                        
            # Copiar pasta DVD por último
            dvd_source = os.path.join(source, "DVD")
            dvd_dest = os.path.join(dest, "DVD")
            
            if os.path.exists(dvd_source):
                os.makedirs(dvd_dest, exist_ok=True)
                remaining_space = shutil.disk_usage(dest)[2]
                
                for game in os.listdir(dvd_source):
                    game_path = os.path.join(dvd_source, game)
                    game_size = self.get_folder_size(game_path) if os.path.isdir(game_path) else os.path.getsize(game_path)
                    
                    if game_size < remaining_space:
                        self.status_label.config(text=f"Copiando jogo: {game}")
                        self.copy_with_progress(game_path, os.path.join(dvd_dest, game))
                        remaining_space -= game_size
                    else:
                        messagebox.showwarning("Aviso", f"Espaço insuficiente para copiar: {game}")
                        break
                        
            self.status_label.config(text="Cópia concluída com sucesso!")
            messagebox.showinfo("Sucesso", "Processo de cópia finalizado!")
            
        except Exception as e:
            self.status_label.config(text="Erro durante a cópia!")
            messagebox.showerror("Erro", str(e))
            
        finally:
            self.progress['value'] = 100
            self.progress_label.config(text="100%")
            
    def start_copy(self):
        if not self.source_path.get() or not self.dest_path.get():
            messagebox.showerror("Erro", "Selecione as pastas de origem e destino!")
            return
            
        self.progress['value'] = 0
        self.progress_label.config(text="0%")
        self.status_label.config(text="Iniciando cópia...")
        
        # Iniciar cópia em uma thread separada para não travar a interface
        thread = threading.Thread(target=self.copy_files)
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = GameCopier(root)
    root.mainloop()