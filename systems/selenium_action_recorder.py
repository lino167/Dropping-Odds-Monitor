#!/usr/bin/env python3
"""
Gravador de Ações Selenium Nativo

Usa as funcionalidades nativas do Selenium para gravar e reproduzir ações.
Baseado no ActionChains e event listeners do Selenium.
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
from selenium.webdriver.support.events import EventFiringWebDriver, AbstractEventListener
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dataclasses import dataclass, asdict
import threading

@dataclass
class SeleniumAction:
    """Ação gravada pelo Selenium."""
    action_type: str  # 'click', 'send_keys', 'navigate', 'wait'
    element_info: Dict[str, str]  # tag, id, class, xpath, text
    value: str  # texto digitado ou URL
    timestamp: str
    screenshot_path: str

@dataclass
class ActionSequence:
    """Sequência de ações gravadas."""
    sequence_id: str
    start_time: str
    end_time: str
    start_url: str
    actions: List[SeleniumAction]
    description: str

class ActionRecorderListener:
    """Listener para capturar eventos reais do usuário via JavaScript."""
    
    def __init__(self):
        self.actions: List[SeleniumAction] = []
        self.is_recording = False
        self.screenshot_counter = 0
        self.screenshots_dir = "screenshots"
        self.driver = None
        self.monitoring_thread = None
        self.stop_monitoring = False
        
        # Cria diretório de screenshots
        os.makedirs(self.screenshots_dir, exist_ok=True)
    
    def start_recording(self, driver):
        """Inicia a gravação de ações."""
        self.is_recording = True
        self.actions.clear()
        self.screenshot_counter = 0
        self.driver = driver
        self.stop_monitoring = False
        
        # Injeta JavaScript para capturar eventos
        self._inject_event_listeners()
        
        # Inicia thread de monitoramento
        self.monitoring_thread = threading.Thread(target=self._monitor_events)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        print("🔴 Gravação iniciada - Execute suas ações no navegador")
    
    def stop_recording(self):
        """Para a gravação de ações."""
        self.is_recording = False
        self.stop_monitoring = True
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1)
        
        print(f"⏹️ Gravação finalizada - {len(self.actions)} ações capturadas")
    
    def _inject_event_listeners(self):
        """Injeta listeners JavaScript para capturar eventos do usuário."""
        js_code = """
        // Remove listeners anteriores se existirem
        if (window.actionRecorderEvents) {
            window.actionRecorderEvents = [];
        } else {
            window.actionRecorderEvents = [];
        }
        
        // Função para capturar informações do elemento
        function getElementInfo(element) {
            return {
                tagName: element.tagName,
                id: element.id || '',
                className: element.className || '',
                text: element.textContent ? element.textContent.substring(0, 50) : '',
                href: element.href || '',
                value: element.value || ''
            };
        }
        
        // Listener para cliques
        document.addEventListener('click', function(event) {
            const elementInfo = getElementInfo(event.target);
            window.actionRecorderEvents.push({
                type: 'click',
                timestamp: new Date().toISOString(),
                element: elementInfo,
                x: event.clientX,
                y: event.clientY,
                url: window.location.href
            });
        }, true);
        
        // Listener para mudanças de input
        document.addEventListener('input', function(event) {
            if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
                const elementInfo = getElementInfo(event.target);
                window.actionRecorderEvents.push({
                    type: 'input',
                    timestamp: new Date().toISOString(),
                    element: elementInfo,
                    value: event.target.value,
                    url: window.location.href
                });
            }
        }, true);
        
        // Listener para mudanças de página
        let currentUrl = window.location.href;
        setInterval(function() {
            if (window.location.href !== currentUrl) {
                window.actionRecorderEvents.push({
                    type: 'navigate',
                    timestamp: new Date().toISOString(),
                    from_url: currentUrl,
                    to_url: window.location.href
                });
                currentUrl = window.location.href;
            }
        }, 500);
        
        console.log('🎯 Event listeners injetados com sucesso!');
        """
        
        try:
            self.driver.execute_script(js_code)
        except Exception as e:
            print(f"⚠️ Erro ao injetar listeners: {e}")
    
    def _monitor_events(self):
        """Monitora eventos capturados pelo JavaScript."""
        while not self.stop_monitoring and self.is_recording:
            try:
                # Recupera eventos do JavaScript
                events = self.driver.execute_script("return window.actionRecorderEvents || [];")
                
                # Processa novos eventos
                for event in events[len(self.actions):]:
                    self._process_js_event(event)
                
                time.sleep(0.5)  # Verifica a cada 500ms
                
            except Exception as e:
                print(f"⚠️ Erro no monitoramento: {e}")
                time.sleep(1)
    
    def _process_js_event(self, event):
        """Processa evento capturado pelo JavaScript."""
        try:
            # Captura screenshot
            screenshot_path = self._take_screenshot()
            
            # Cria informações do elemento
            element_info = event.get('element', {})
            
            # Cria ação
            action = SeleniumAction(
                action_type=event['type'],
                element_info=element_info,
                value=event.get('value', event.get('to_url', '')),
                timestamp=event['timestamp'],
                screenshot_path=screenshot_path
            )
            
            self.actions.append(action)
            
            # Log da ação
            element_desc = element_info.get('text', element_info.get('id', element_info.get('tagName', 'elemento')))
            print(f"   📝 {event['type']}: {element_desc[:30]}")
            
        except Exception as e:
            print(f"   ⚠️ Erro ao processar evento: {e}")
    
    def _record_action(self, action_type: str, element, driver, value: str = ""):
        """Grava uma ação."""
        try:
            # Captura informações do elemento
            element_info = {}
            if element:
                element_info = {
                    'tag_name': element.tag_name,
                    'id': element.get_attribute('id') or '',
                    'class': element.get_attribute('class') or '',
                    'text': element.text[:50] if element.text else '',
                    'xpath': self._get_xpath(element, driver)
                }
            
            # Captura screenshot
            screenshot_path = self._take_screenshot(driver)
            
            # Cria ação
            action = SeleniumAction(
                action_type=action_type,
                element_info=element_info,
                value=value,
                timestamp=datetime.now().isoformat(),
                screenshot_path=screenshot_path
            )
            
            self.actions.append(action)
            print(f"   📝 Ação gravada: {action_type} - {element_info.get('text', value)[:30]}")
            
        except Exception as e:
            print(f"   ⚠️ Erro ao gravar ação: {str(e)}")
    
    def _get_xpath(self, element, driver) -> str:
        """Gera XPath para o elemento."""
        try:
            return driver.execute_script(
                "function getXPath(element) {"
                "  if (element.id !== '') {"
                "    return `//*[@id='${element.id}']`;"
                "  }"
                "  if (element === document.body) {"
                "    return '/html/body';"
                "  }"
                "  let ix = 0;"
                "  const siblings = element.parentNode.childNodes;"
                "  for (let i = 0; i < siblings.length; i++) {"
                "    const sibling = siblings[i];"
                "    if (sibling === element) {"
                "      return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';"
                "    }"
                "    if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {"
                "      ix++;"
                "    }"
                "  }"
                "}"
                "return getXPath(arguments[0]);", element
            )
        except:
            return ""
    
    def _take_screenshot(self) -> str:
        """Captura screenshot da ação."""
        try:
            self.screenshot_counter += 1
            filename = f"action_{self.screenshot_counter:03d}_{datetime.now().strftime('%H%M%S')}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            if self.driver:
                self.driver.save_screenshot(filepath)
            return filepath
        except:
            return ""

class SeleniumActionRecorder:
    """Gravador de ações usando Selenium nativo."""
    
    def __init__(self):
        self.driver = None
        self.event_driver = None
        self.listener = ActionRecorderListener()
        self.current_sequence: Optional[ActionSequence] = None
    
    def setup_driver(self, headless: bool = False):
        """Configura o driver Chrome."""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1200,800')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Cria driver
        self.driver = webdriver.Chrome(options=chrome_options)
        
        print("🚀 Driver configurado com gravação de eventos")
    
    def start_interactive_session(self, url: str = "https://dropping-odds.com/index.php?view=live"):
        """Inicia sessão interativa de gravação."""
        if not self.driver:
            self.setup_driver()
        
        print(f"\n🎯 SESSÃO INTERATIVA DE GRAVAÇÃO")
        print(f"URL: {url}")
        print("=" * 50)
        
        # Navega para URL inicial
        self.driver.get(url)
        time.sleep(2)
        
        # Cria nova sequência
        sequence_id = f"seq_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_sequence = ActionSequence(
            sequence_id=sequence_id,
            start_time=datetime.now().isoformat(),
            end_time="",
            start_url=url,
            actions=[],
            description="Sessão interativa de gravação"
        )
        
        # Interface de controle via terminal
        self._run_interactive_control()
    
    def _run_interactive_control(self):
        """Executa controle interativo via terminal."""
        print("\n📋 COMANDOS DISPONÍVEIS:")
        print("  'start' ou 's' - Iniciar gravação")
        print("  'stop' ou 'p' - Parar gravação")
        print("  'replay' ou 'r' - Reproduzir ações")
        print("  'save' - Salvar sequência")
        print("  'load' - Carregar sequência")
        print("  'status' - Ver status atual")
        print("  'quit' ou 'q' - Sair")
        print("\n💡 Dica: Deixe o navegador aberto e execute ações normalmente")
        
        while True:
            try:
                command = input("\n> ").strip().lower()
                
                if command in ['start', 's']:
                    self.listener.start_recording(self.driver)
                
                elif command in ['stop', 'p']:
                    self.listener.stop_recording()
                    self.current_sequence.actions = self.listener.actions.copy()
                    self.current_sequence.end_time = datetime.now().isoformat()
                
                elif command in ['replay', 'r']:
                    if self.current_sequence and self.current_sequence.actions:
                        self._replay_sequence()
                    else:
                        print("❌ Nenhuma sequência para reproduzir")
                
                elif command == 'save':
                    if self.current_sequence:
                        filename = input("Nome do arquivo (sem extensão): ").strip()
                        if not filename:
                            filename = f"sequence_{self.current_sequence.sequence_id}"
                        self._save_sequence(f"{filename}.json")
                    else:
                        print("❌ Nenhuma sequência para salvar")
                
                elif command == 'load':
                    filename = input("Nome do arquivo: ").strip()
                    if os.path.exists(filename):
                        self._load_sequence(filename)
                    else:
                        print(f"❌ Arquivo não encontrado: {filename}")
                
                elif command == 'status':
                    self._show_status()
                
                elif command in ['quit', 'q']:
                    break
                
                else:
                    print("❌ Comando não reconhecido")
            
            except KeyboardInterrupt:
                print("\n⏹️ Sessão interrompida")
                break
            except Exception as e:
                print(f"❌ Erro: {str(e)}")
        
        self._cleanup()
    
    def _replay_sequence(self):
        """Reproduz a sequência atual."""
        if not self.current_sequence or not self.current_sequence.actions:
            print("❌ Nenhuma sequência para reproduzir")
            return
        
        print(f"▶️ Reproduzindo {len(self.current_sequence.actions)} ações...")
        
        try:
            # Navega para URL inicial
            self.driver.get(self.current_sequence.start_url)
            time.sleep(2)
            
            # Executa cada ação
            for i, action in enumerate(self.current_sequence.actions, 1):
                print(f"   Ação {i}/{len(self.current_sequence.actions)}: {action.action_type}")
                
                try:
                    if action.action_type == 'click':
                        self._replay_click(action)
                    elif action.action_type == 'send_keys':
                        self._replay_send_keys(action)
                    elif action.action_type == 'navigate':
                        self.driver.get(action.value)
                    
                    time.sleep(1)  # Pausa entre ações
                    
                except Exception as e:
                    print(f"   ⚠️ Erro na ação {i}: {str(e)}")
                    continue
            
            print("✅ Reprodução concluída")
            
        except Exception as e:
            print(f"❌ Erro na reprodução: {str(e)}")
    
    def _replay_click(self, action: SeleniumAction):
        """Reproduz um clique."""
        element_info = action.element_info
        
        # Tenta diferentes estratégias para encontrar o elemento
        element = None
        
        # 1. Por ID
        if element_info.get('id'):
            try:
                element = self.driver.find_element(By.ID, element_info['id'])
            except:
                pass
        
        # 2. Por XPath
        if not element and element_info.get('xpath'):
            try:
                element = self.driver.find_element(By.XPATH, element_info['xpath'])
            except:
                pass
        
        # 3. Por texto
        if not element and element_info.get('text'):
            try:
                element = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{element_info['text'][:20]}')]") 
            except:
                pass
        
        # 4. Por classe
        if not element and element_info.get('class'):
            try:
                elements = self.driver.find_elements(By.CLASS_NAME, element_info['class'].split()[0])
                if elements:
                    element = elements[0]
            except:
                pass
        
        if element:
            ActionChains(self.driver).click(element).perform()
        else:
            raise Exception(f"Elemento não encontrado: {element_info}")
    
    def _replay_send_keys(self, action: SeleniumAction):
        """Reproduz digitação."""
        element_info = action.element_info
        
        # Encontra elemento (mesmo processo do clique)
        element = None
        
        if element_info.get('id'):
            try:
                element = self.driver.find_element(By.ID, element_info['id'])
            except:
                pass
        
        if not element and element_info.get('xpath'):
            try:
                element = self.driver.find_element(By.XPATH, element_info['xpath'])
            except:
                pass
        
        if element:
            element.clear()
            element.send_keys(action.value)
        else:
            raise Exception(f"Campo de texto não encontrado: {element_info}")
    
    def _save_sequence(self, filename: str):
        """Salva sequência em arquivo."""
        try:
            sequence_data = asdict(self.current_sequence)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(sequence_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Sequência salva: {filename}")
            
        except Exception as e:
            print(f"❌ Erro ao salvar: {str(e)}")
    
    def _load_sequence(self, filename: str):
        """Carrega sequência de arquivo."""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                sequence_data = json.load(f)
            
            # Reconstrói ações
            actions = []
            for action_data in sequence_data['actions']:
                action = SeleniumAction(**action_data)
                actions.append(action)
            
            # Reconstrói sequência
            sequence_data['actions'] = actions
            self.current_sequence = ActionSequence(**sequence_data)
            
            print(f"📂 Sequência carregada: {filename} ({len(self.current_sequence.actions)} ações)")
            
        except Exception as e:
            print(f"❌ Erro ao carregar: {str(e)}")
    
    def _show_status(self):
        """Mostra status atual."""
        print(f"\n📊 STATUS ATUAL:")
        print(f"Gravando: {'🔴 SIM' if self.listener.is_recording else '⚪ NÃO'}")
        
        if self.current_sequence:
            print(f"Sequência: {self.current_sequence.sequence_id}")
            print(f"Ações gravadas: {len(self.current_sequence.actions)}")
            print(f"URL inicial: {self.current_sequence.start_url}")
            
            if self.current_sequence.actions:
                print(f"\nÚltimas ações:")
                for action in self.current_sequence.actions[-3:]:
                    print(f"  - {action.action_type}: {action.element_info.get('text', action.value)[:30]}")
        else:
            print("Nenhuma sequência ativa")
    
    def _cleanup(self):
        """Limpa recursos."""
        if self.driver:
            self.driver.quit()
        print("🔒 Sessão finalizada")

# Função principal
def main():
    """Função principal."""
    print("🎯 Gravador de Ações Selenium Nativo")
    print("=" * 40)
    
    recorder = SeleniumActionRecorder()
    
    try:
        # URL específica do evento para análise
        url = "https://dropping-odds.com/event.php?id=10387420&t=1x2"
        
        print(f"\n📍 Navegando automaticamente para: {url}")
        print("\n🔴 GRAVAÇÃO AUTOMÁTICA ATIVADA")
        print("\n📝 Todas as suas ações serão gravadas automaticamente:")
        print("  • Cliques em qualquer elemento")
        print("  • Navegação para outras páginas")
        print("  • Interações com formulários")
        print("  • Scrolling e movimentos")
        
        # Inicia sessão interativa
        recorder.start_interactive_session(url)
        
    except KeyboardInterrupt:
        print("\n⏹️ Execução interrompida")
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")

if __name__ == "__main__":
    main()