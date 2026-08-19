# 📡 Router Monitor — TP-Link Archer C5W

Monitor de métricas para roteadores TP-Link via Telnet. Coleta uptime, uso de RAM,
estatísticas da interface WAN e dispositivos WiFi conectados.

## 📋 Funcionalidades

- ✅ Conexão Telnet efêmera (abre → executa → fecha)
- ✅ Extração de uptime do sistema
- ✅ Monitoramento de memória RAM (total/livre)
- ✅ Estatísticas de tráfego WAN (RX/TX)
- ✅ Lista de dispositivos WiFi conectados (MAC, sinal, velocidade)
- ✅ Proteção de credenciais via `.env`

## 🔧 Requisitos

- Python 3.10+ (para `telnetlib` da stdlib)
- Roteador com Telnet habilitado
- Acesso à rede local

## 🚀 Instalação

```bash
# Clone o repositório
git clone https://github.com/johnrego/router-monitor.git
cd router-monitor

# Crie um ambiente virtual
python -m venv .venv
source .venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

# Configure as credenciais
cp .env.example .env
nano .env  # Preencha com a senha do modem
