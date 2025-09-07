#!/usr/bin/env python3
"""
Sistema Interativo de Gravação de Cliques

Este script permite ao usuário:
1. Abrir um navegador e navegar manualmente
2. Gravar sequências de cliques e ações
3. Reproduzir automaticamente as ações gravadas
4. Extrair dados baseado no fluxo gravado
"""

import time
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dataclasses import dataclass, asdict
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading

@dataclass
class ClickAction:
    """Representa uma ação de clique gravada."""
    action_type: str  # 'click', 'type', 'wait', 'scroll', 'navigate'
    element_selector: str
    element_text: str
    coordinates: Tuple[int, int]
    timestamp: str
    wait_time: float
    additional_data: Dict[str, Any]

@dataclass
class RecordingSession:
    """Sessão de gravação completa."""
    session_id: str
    start_time: str
    end_time: str
    actions: List[ClickAction]
    url_start: str
    description: str
    success: bool

class ClickRecorderGUI:
    """Interface gráfica para controle da gravação."""
    
    def __init__(self, recorder):
        self.recorder = recorder
        self.root = tk.Tk()
        self.root.title("Gravador de Cliques - Extração de Dados")
        self.root.geometry("500x600")
        self.root.attributes('-topmost', True)  # Sempre no topo
        
        self.setup_gui()
        
    def setup_gui(self):
        """Configura a interface gráfica."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título
        title_label = ttk.Label(main_frame, text="🎯 Gravador de Cliques", font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # URL inicial
        ttk.Label(main_frame, text="URL Inicial:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.url_var = tk.StringVar(value="https://dropping-odds.com/index.php?view=live")
        url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=50)
        url_entry.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # Descrição da sessão
        ttk.Label(main_frame, text="Descrição:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.desc_var = tk.StringVar(value="Gravação de fluxo de extração")
        desc_entry = ttk.Entry(main_frame, textvariable=self.desc_var, width=50)
        desc_entry.grid(row=2, column=1, pady=5, padx=(10, 0))
        
        # Botões de controle
        control_frame = ttk.LabelFrame(main_frame, text="Controles", padding="10")
        control_frame.grid(row=3, column=0, columnspan=2, pady=20, sticky=(tk.W, tk.E))
        
        self.start_btn = ttk.Button(control_frame, text="🚀 Iniciar Navegador", 
                                   command=self.start_browser, style='Accent.TButton')
        self.start_btn.grid(row=0, column=0, padx=5, pady=5)
        
        self.record_btn = ttk.Button(control_frame, text="⏺️ Iniciar Gravação", 
                                    command=self.start_recording, state='disabled')
        self.record_btn.grid(row=0, column=1, padx=5, pady=5)
        
        self.stop_btn = ttk.Button(control_frame, text="⏹️ Parar Gravação", 
                                  command=self.stop_recording, state='disabled')
        self.stop_btn.grid(row=0, column=2, padx=5, pady=5)
        
        self.replay_btn = ttk.Button(control_frame, text="▶️ Reproduzir", 
                                    command=self.replay_actions, state='disabled')
        self.replay_btn.grid(row=1, column=0, padx=5, pady=5)
        
        self.save_btn = ttk.Button(control_frame, text="💾 Salvar Sessão", 
                                  command=self.save_session, state='disabled')
        self.save_btn.grid(row=1, column=1, padx=5, pady=5)
        
        self.load_btn = ttk.Button(control_frame, text="📂 Carregar Sessão", 
                                  command=self.load_session)
        self.load_btn.grid(row=1, column=2, padx=5, pady=5)
        
        # Status
        self.status_var = tk.StringVar(value="Pronto para iniciar")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, 
                                font=('Arial', 10), foreground='blue')
        status_label.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Lista de ações gravadas
        actions_frame = ttk.LabelFrame(main_frame, text="Ações Gravadas", padding="10")
        actions_frame.grid(row=5, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Treeview para mostrar ações
        self.actions_tree = ttk.Treeview(actions_frame, columns=('Tipo', 'Elemento', 'Tempo'), 
                                        show='tree headings', height=10)
        self.actions_tree.heading('#0', text='#')
        self.actions_tree.heading('Tipo', text='Tipo')
        self.actions_tree.heading('Elemento', text='Elemento')
        self.actions_tree.heading('Tempo', text='Tempo')
        
        self.actions_tree.column('#0', width=50)
        self.actions_tree.column('Tipo', width=100)
        self.actions_tree.column('Elemento', width=200)
        self.actions_tree.column('Tempo', width=100)
        
        scrollbar = ttk.Scrollbar(actions_frame, orient=tk.VERTICAL, command=self.actions_tree.yview)
        self.actions_tree.configure(yscrollcommand=scrollbar.set)
        
        self.actions_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Instruções
        instructions = (
            "📋 INSTRUÇÕES:\n"
            "1. Digite a URL inicial e descrição\n"
            "2. Clique em 'Iniciar Navegador'\n"
            "3. Clique em 'Iniciar Gravação'\n"
            "4. Navegue e clique normalmente no site\n"
            "5. Clique em 'Parar Gravação' quando terminar\n"
            "6. Use 'Reproduzir' para testar a automação\n"
            "7. Salve a sessão para uso futuro"
        )
        
        instructions_label = ttk.Label(main_frame, text=instructions, 
                                      font=('Arial', 9), justify=tk.LEFT)
        instructions_label.grid(row=6, column=0, columnspan=2, pady=20, sticky=tk.W)
        
        # Configurar redimensionamento
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
        actions_frame.columnconfigure(0, weight=1)
        actions_frame.rowconfigure(0, weight=1)
    
    def start_browser(self):
        """Inicia o navegador."""
        try:
            self.recorder.setup_driver()
            self.recorder.driver.get(self.url_var.get())
            
            self.status_var.set("Navegador iniciado - Pronto para gravar")
            self.start_btn.config(state='disabled')
            self.record_btn.config(state='normal')
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao iniciar navegador: {str(e)}")
    
    def start_recording(self):
        """Inicia a gravação de ações."""
        self.recorder.start_recording(self.desc_var.get())
        self.status_var.set("🔴 GRAVANDO - Clique normalmente no navegador")
        
        self.record_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        
        # Inicia thread para monitorar ações
        self.monitor_thread = threading.Thread(target=self.monitor_actions, daemon=True)
        self.monitor_thread.start()
    
    def stop_recording(self):
        """Para a gravação."""
        self.recorder.stop_recording()
        self.status_var.set("Gravação finalizada")
        
        self.stop_btn.config(state='disabled')
        self.replay_btn.config(state='normal')
        self.save_btn.config(state='normal')
        
        self.update_actions_list()
    
    def monitor_actions(self):
        """Monitora ações em thread separada."""
        while self.recorder.is_recording:
            time.sleep(0.5)
            # Atualiza lista de ações em tempo real
            self.root.after(0, self.update_actions_list)
    
    def update_actions_list(self):
        """Atualiza a lista de ações na interface."""
        # Limpa lista atual
        for item in self.actions_tree.get_children():
            self.actions_tree.delete(item)
        
        # Adiciona ações gravadas
        if self.recorder.current_session:
            for i, action in enumerate(self.recorder.current_session.actions, 1):
                self.actions_tree.insert('', 'end', text=str(i),
                                        values=(action.action_type, 
                                               action.element_text[:30] + '...' if len(action.element_text) > 30 else action.element_text,
                                               f"{action.wait_time:.1f}s"))
    
    def replay_actions(self):
        """Reproduz as ações gravadas."""
        if not self.recorder.current_session:
            messagebox.showwarning("Aviso", "Nenhuma sessão para reproduzir")
            return
        
        self.status_var.set("▶️ Reproduzindo ações...")
        
        # Executa reprodução em thread separada
        replay_thread = threading.Thread(target=self._replay_thread, daemon=True)
        replay_thread.start()
    
    def _replay_thread(self):
        """Thread para reprodução de ações."""
        try:
            success = self.recorder.replay_session()
            if success:
                self.root.after(0, lambda: self.status_var.set("✅ Reprodução concluída com sucesso"))
            else:
                self.root.after(0, lambda: self.status_var.set("❌ Erro na reprodução"))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"❌ Erro: {str(e)}"))
    
    def save_session(self):
        """Salva a sessão atual."""
        if not self.recorder.current_session:
            messagebox.showwarning("Aviso", "Nenhuma sessão para salvar")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Salvar Sessão de Gravação"
        )
        
        if filename:
            try:
                self.recorder.save_session(filename)
                messagebox.showinfo("Sucesso", f"Sessão salva em: {filename}")
                self.status_var.set(f"Sessão salva: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar: {str(e)}")
    
    def load_session(self):
        """Carrega uma sessão salva."""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Carregar Sessão de Gravação"
        )
        
        if filename:
            try:
                self.recorder.load_session(filename)
                self.update_actions_list()
                self.replay_btn.config(state='normal')
                messagebox.showinfo("Sucesso", f"Sessão carregada: {os.path.basename(filename)}")
                self.status_var.set(f"Sessão carregada: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar: {str(e)}")
    
    def run(self):
        """Executa a interface gráfica."""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """Chamado ao fechar a janela."""
        if self.recorder.driver:
            self.recorder.close_driver()
        self.root.destroy()

class InteractiveClickRecorder:
    """Sistema principal de gravação de cliques."""
    
    def __init__(self):
        self.driver = None
        self.wait = None
        self.is_recording = False
        self.current_session: Optional[RecordingSession] = None
        self.last_action_time = time.time()
        
    def setup_driver(self):
        """Configura o driver do Selenium."""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1200,800')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Adiciona extensão para capturar cliques
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
        # Injeta JavaScript para capturar cliques
        self.inject_click_capture_script()
    
    def inject_click_capture_script(self):
        """Injeta script JavaScript para capturar cliques."""
        script = """
        window.recordedClicks = [];
        
        function captureClick(event) {
            if (window.isRecording) {
                const element = event.target;
                const rect = element.getBoundingClientRect();
                
                const clickData = {
                    tagName: element.tagName,
                    className: element.className,
                    id: element.id,
                    text: element.textContent.trim().substring(0, 50),
                    xpath: getXPath(element),
                    x: event.clientX,
                    y: event.clientY,
                    timestamp: Date.now()
                };
                
                window.recordedClicks.push(clickData);
            }
        }
        
        function getXPath(element) {
            if (element.id !== '') {
                return `//*[@id="${element.id}"]`;
            }
            if (element === document.body) {
                return '/html/body';
            }
            
            let ix = 0;
            const siblings = element.parentNode.childNodes;
            for (let i = 0; i < siblings.length; i++) {
                const sibling = siblings[i];
                if (sibling === element) {
                    return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                }
                if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                    ix++;
                }
            }
        }
        
        document.addEventListener('click', captureClick, true);
        window.isRecording = false;
        """
        
        self.driver.execute_script(script)
    
    def start_recording(self, description: str):
        """Inicia uma nova sessão de gravação."""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_session = RecordingSession(
            session_id=session_id,
            start_time=datetime.now().isoformat(),
            end_time="",
            actions=[],
            url_start=self.driver.current_url,
            description=description,
            success=False
        )
        
        self.is_recording = True
        self.last_action_time = time.time()
        
        # Ativa captura no JavaScript
        self.driver.execute_script("window.isRecording = true;")
        
        print(f"🎬 Gravação iniciada: {session_id}")
    
    def stop_recording(self):
        """Para a gravação atual."""
        if not self.is_recording or not self.current_session:
            return
        
        self.is_recording = False
        
        # Para captura no JavaScript
        self.driver.execute_script("window.isRecording = false;")
        
        # Coleta cliques capturados
        self.collect_recorded_clicks()
        
        # Finaliza sessão
        self.current_session.end_time = datetime.now().isoformat()
        self.current_session.success = True
        
        print(f"🎬 Gravação finalizada: {len(self.current_session.actions)} ações gravadas")
    
    def collect_recorded_clicks(self):
        """Coleta cliques gravados do JavaScript."""
        try:
            clicks = self.driver.execute_script("return window.recordedClicks || [];")
            
            for click in clicks:
                action = ClickAction(
                    action_type='click',
                    element_selector=click.get('xpath', ''),
                    element_text=click.get('text', ''),
                    coordinates=(click.get('x', 0), click.get('y', 0)),
                    timestamp=datetime.fromtimestamp(click.get('timestamp', 0) / 1000).isoformat(),
                    wait_time=1.0,  # Tempo padrão entre ações
                    additional_data={
                        'tag_name': click.get('tagName', ''),
                        'class_name': click.get('className', ''),
                        'element_id': click.get('id', '')
                    }
                )
                
                self.current_session.actions.append(action)
            
            # Limpa cliques coletados
            self.driver.execute_script("window.recordedClicks = [];")
            
        except Exception as e:
            print(f"⚠️ Erro ao coletar cliques: {str(e)}")
    
    def replay_session(self) -> bool:
        """Reproduz uma sessão gravada."""
        if not self.current_session:
            print("❌ Nenhuma sessão para reproduzir")
            return False
        
        print(f"▶️ Reproduzindo sessão: {self.current_session.session_id}")
        
        try:
            # Navega para URL inicial
            self.driver.get(self.current_session.url_start)
            time.sleep(2)
            
            # Executa cada ação
            for i, action in enumerate(self.current_session.actions, 1):
                print(f"   Ação {i}/{len(self.current_session.actions)}: {action.action_type}")
                
                try:
                    if action.action_type == 'click':
                        self.replay_click_action(action)
                    elif action.action_type == 'type':
                        self.replay_type_action(action)
                    elif action.action_type == 'wait':
                        time.sleep(action.wait_time)
                    
                    # Aguarda entre ações
                    time.sleep(action.wait_time)
                    
                except Exception as e:
                    print(f"   ⚠️ Erro na ação {i}: {str(e)}")
                    continue
            
            print("✅ Reprodução concluída")
            return True
            
        except Exception as e:
            print(f"❌ Erro na reprodução: {str(e)}")
            return False
    
    def replay_click_action(self, action: ClickAction):
        """Reproduz uma ação de clique."""
        try:
            # Tenta encontrar elemento pelo XPath
            if action.element_selector:
                element = self.wait.until(EC.element_to_be_clickable((By.XPATH, action.element_selector)))
                element.click()
            else:
                # Fallback: clique por coordenadas
                ActionChains(self.driver).move_by_offset(
                    action.coordinates[0], action.coordinates[1]
                ).click().perform()
                
        except Exception as e:
            print(f"   ⚠️ Erro no clique: {str(e)}")
            raise
    
    def replay_type_action(self, action: ClickAction):
        """Reproduz uma ação de digitação."""
        try:
            element = self.wait.until(EC.presence_of_element_located((By.XPATH, action.element_selector)))
            element.clear()
            element.send_keys(action.element_text)
            
        except Exception as e:
            print(f"   ⚠️ Erro na digitação: {str(e)}")
            raise
    
    def save_session(self, filename: str):
        """Salva a sessão atual em arquivo JSON."""
        if not self.current_session:
            raise ValueError("Nenhuma sessão para salvar")
        
        session_data = asdict(self.current_session)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Sessão salva: {filename}")
    
    def load_session(self, filename: str):
        """Carrega uma sessão de arquivo JSON."""
        with open(filename, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        # Reconstrói objetos ClickAction
        actions = []
        for action_data in session_data['actions']:
            action = ClickAction(**action_data)
            actions.append(action)
        
        # Reconstrói sessão
        session_data['actions'] = actions
        self.current_session = RecordingSession(**session_data)
        
        print(f"📂 Sessão carregada: {filename}")
    
    def close_driver(self):
        """Fecha o driver."""
        if self.driver:
            self.driver.quit()
            print("🔒 Navegador fechado")

# Função principal
def main():
    """Função principal para executar o gravador interativo."""
    print("🎯 Sistema Interativo de Gravação de Cliques")
    print("=" * 50)
    
    # Cria recorder e interface
    recorder = InteractiveClickRecorder()
    gui = ClickRecorderGUI(recorder)
    
    try:
        # Executa interface gráfica
        gui.run()
        
    except KeyboardInterrupt:
        print("\n⏹️ Execução interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro na execução: {str(e)}")
    finally:
        recorder.close_driver()

if __name__ == "__main__":
    main()