#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor de Modem TP-Link Archer C5
Coleta métricas via Telnet e extrai informações relevantes.
"""

import os
import re
import telnetlib
from dataclasses import dataclass, field
from time import sleep
from dotenv import load_dotenv

load_dotenv()
ROUTER_HOST = os.getenv("modemIP", "")
ROUTER_PASS = os.getenv("modemPass", "")
TIMEOUT = 8

@dataclass
class RouterMetrics:
    """Métricas extraídas do roteador."""
    uptime_seconds: int = 0
    mem_free_kb: int = 0
    mem_total_kb: int = 0
    wan_ip: str = ""
    wan_rx_bytes: int = 0
    wan_tx_bytes: int = 0
    connected_devices: list = field(default_factory=list)

class TelnetSession:
    """
    Sessão telnet efêmera:
    connect → login → execute → close
    """

    def __init__(self, host: str, password: str):
        self.host = host
        self.password = password
        self.tn = None

    def _open(self):
        """Abre a conexão e faz o login."""
        self.tn = telnetlib.Telnet(self.host, timeout=TIMEOUT)
        self.tn.read_until(b"Password:", timeout=TIMEOUT)
        self.tn.write(self.password.encode("ascii") + b"\n")
        sleep(1)

    def _close(self):
        """Encerra a sessão de forma segura."""
        if self.tn:
            try:
                self.tn.write(b"exit\n")
                sleep(0.3)
            except Exception:
                pass
            try:
                self.tn.close()
            except Exception:
                pass
            self.tn = None

    def execute(self, command: str) -> str:
        """
        Ciclo completo:
          1. abre conexão
          2. loga
          3. envia 1 comando
          4. lê a saída
          5. fecha
        """
        output = ""
        try:
            self._open()
            self.tn.write(command.encode("ascii") + b"\n")
            sleep(3)
            output = self.tn.read_very_eager().decode("ascii", errors="ignore")
        except ConnectionRefusedError:
            output = "[erro] Conexão recusada pelo modem."
        except TimeoutError:
            output = "[erro] Timeout: o modem não respondeu a tempo."
        except Exception as e:
            output = f"[erro] {type(e).__name__}: {e}"
        finally:
            self._close()
        return output

class RouterParser:
    """
    Extrai métricas da saída do 'debug sysinfo'.
    """

    def parse(self, raw_output: str) -> RouterMetrics:
        """Parseia a saída completa."""
        metrics = RouterMetrics()
        lines = raw_output.splitlines()
        in_wan_section = False

        for i, line in enumerate(lines):
            # ── Uptime ──
            if "System Uptime:" in line:
                metrics.uptime_seconds = self._extract_int(line, "System Uptime:")

            # ── Memória ──
            elif "MemTotal:" in line:
                metrics.mem_total_kb = self._extract_int(line, "MemTotal:")
            elif "MemFree:" in line:
                metrics.mem_free_kb = self._extract_int(line, "MemFree:")

            # ── Início da seção WAN (eth0.2) ──
            elif "eth0.2" in line and "Link encap:Ethernet" in line:
                in_wan_section = True

            # ── Fim da seção WAN (próxima interface) ──
            elif in_wan_section and re.match(r'^(eth0\.\d|lo|ra\d|rai\d)\s', line):
                in_wan_section = False

            # ── IP WAN ──
            elif in_wan_section and "inet addr:" in line:
                match = re.search(r'inet addr:(\S+)', line)
                if match:
                    metrics.wan_ip = match.group(1)

            # ── Estatísticas RX/TX da WAN ──
            elif in_wan_section and "RX bytes:" in line:
                rx = re.search(r'RX bytes:(\d+)', line)
                tx = re.search(r'TX bytes:(\d+)', line)
                if rx:
                    metrics.wan_rx_bytes = int(rx.group(1))
                if tx:
                    metrics.wan_tx_bytes = int(tx.group(1))

            # ── Dispositivos WiFi conectados ──
            elif "AssociatedDeviceMACAddress" in line:
                match = re.search(r'>([A-F0-9:]{17})<', line)
                if match:
                    metrics.connected_devices.append(match.group(1))

        return metrics

    @staticmethod
    def _extract_int(line: str, prefix: str) -> int:
        match = re.search(rf'{re.escape(prefix)}\s+(\d+)', line)
        if not match:
            print(f"⚠️  Não consegui extrair '{prefix}' da linha: {line!r}")
            return 0
        return int(match.group(1))

    @staticmethod
    def format_report(m: RouterMetrics) -> str:
        """Formata as métricas em um relatório legível."""
        uptime_d = m.uptime_seconds // 86400
        uptime_h = (m.uptime_seconds % 86400) // 3600
        uptime_m = (m.uptime_seconds % 3600) // 60

        lines = [
            "═" * 52,
            "  📊 RELATÓRIO DO ROTEADOR — TP-Link Archer C5",
            "═" * 52,
            f"  ⏱  Uptime:         {uptime_d}d {uptime_h}h {uptime_m}m ({m.uptime_seconds}s)",
            f"  💾 RAM Total:      {m.mem_total_kb} kB ({m.mem_total_kb / 1024:.1f} MB)",
            f"  💾 RAM Livre:      {m.mem_free_kb} kB ({m.mem_free_kb / 1024:.1f} MB)",
            f"  🌐 IP WAN:         {m.wan_ip or 'N/A'}",
            f"  📥 RX:             {m.wan_rx_bytes / (1024**2):.1f} MB",
            f"  📤 TX:             {m.wan_tx_bytes / (1024**2):.1f} MB",
            f"  📱 Dispositivos:   {len(m.connected_devices)}",
        ]

        for mac in m.connected_devices:
            lines.append(f"     • {mac}")

        lines.append("═" * 52)
        return "\n".join(lines)

if __name__ == "__main__":
    if not ROUTER_PASS:
        print("❌ Variável de ambiente 'modemPass' não definida.")
        print("   Crie um arquivo .env com: modemPass=sua_senha")
        raise SystemExit(1)

    device = TelnetSession(ROUTER_HOST, ROUTER_PASS)
    raw = device.execute("debug sysinfo")

    if raw.startswith("[erro]") or raw.startswith("[timeout]"):
        print(raw)
        raise SystemExit(1)

    parser = RouterParser()
    metrics = parser.parse(raw)
    print(parser.format_report(metrics))