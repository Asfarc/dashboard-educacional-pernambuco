# Este arquivo existe para compatibilidade com a plataforma de hospedagem
import sys
import os

# Adiciona o diretório atual ao path para encontrar os módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Agora importa o app
import app
