![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python) ![Scapy](https://img.shields.io/badge/Scapy-2.x-green) ![GNS3](https://img.shields.io/badge/GNS3-vIOS--L2-orange) ![Lab](https://img.shields.io/badge/Lab-EGALDITO__LAB-red)

# DHCP Spoofing Attack

> **Autor:** Edgardy Olivero | **Matrícula:** 20250704
> **Laboratorio:** EGALDITO\_LAB | **Herramienta:** Python 3 + Scapy
> **Repositorio:** [github.com/Edgardy715/DHCP-spoofing](https://github.com/Edgardy715/DHCP-spoofing)

---

## 📋 Objetivo del Laboratorio

Demostrar cómo un atacante puede desplegar un servidor DHCP fraudulento (rogue) que responda antes que el servidor legítimo, asignando a los clientes una puerta de enlace y DNS falsos controlados por el atacante. El resultado es una posición de Man-in-the-Middle pasiva sobre el tráfico de los nuevos clientes DHCP, sin necesidad de modificar ninguna configuración en los equipos víctima.

---

## 🎯 Objetivo del Script

Escuchar solicitudes DHCP Discover en VLAN 10, responder con DHCP Offer y ACK que asignan la IP del atacante como gateway y DNS, completar el handshake DORA completo y mantener un pool de IPs falsas asignadas por MAC de cliente. El script actúa como servidor DHCP rogue y compite con el servidor legítimo (R1) respondiendo primero.

---

## 📁 Estructura del Repositorio

```text
DHCP-spoofing/
├── Script/
│   └── DHCP-Spoofing.py                  ← Script principal del ataque
├── Mitigacion/
│   └── Mitigacion-DHCP-Spoofing.ios      ← Comandos DHCP Snooping (Cisco IOS)
├── Conf-Topologia/
│   └── scripts_bases_configs/
│       ├── R1.ios
│       ├── SW1-VTPSERVER.ios
│       └── SW2.ios
├── Topologia/
│   └── Topologia.png
└── README.md
```

---

## ⚙️ Parámetros del Script

| Variable | Valor | Descripción |
|---|---|---|
| `IFACE` | `eth0.10` | Subinterfaz VLAN 10 del atacante. |
| `FAKE_GW` | `192.168.10.2` | IP falsa anunciada como gateway (IP del atacante). |
| `FAKE_DNS` | `192.168.10.2` | IP falsa anunciada como servidor DNS. |
| `SUBNET` | `255.255.255.0` | Máscara de subred asignada a los clientes. |
| `POOL` | `192.168.10.100–149` | Rango de IPs que entrega el servidor rogue. |
| `lease_time` | `3600` | Duración de la concesión en segundos (1 hora). |
| `asignado` | `dict {mac: ip}` | Registro de IPs entregadas por MAC de cliente. |

---

## 🛠️ Requisitos

```bash
# Dependencias
pip install scapy

# Crear subinterfaz VLAN 10
ip link add link eth0 name eth0.10 type vlan id 10
ip link set eth0.10 up

# Asignar IP al atacante en VLAN 10
ip addr add 192.168.10.2/24 dev eth0.10

# Ejecutar como root
sudo python3 Script/DHCP-Spoofing.py
```

---

## 🔍 Funcionamiento del Script

### Flujo de ejecución

```text
1. Verifica privilegios root.
2. sniff() escucha en eth0.10 filtrando udp port 67.
3. dhcp_handler() procesa cada paquete entrante:
   |── DHCP Discover (tipo 1):
   |   → asigna una IP del POOL a la MAC del cliente.
   |   → envía DHCP Offer con FAKE_GW y FAKE_DNS.
   └── DHCP Request (tipo 3):
       → recupera la IP previamente asignada.
       → envía DHCP ACK confirmando la concesión.
4. Ctrl+C → cleanup(): imprime total de IPs asignadas.
```

### Intercambio DORA modificado

```text
Cliente            Atacante (servidor rogue)       R1 (servidor legítimo)
   |─── Discover ──►|
   |◄── Offer ───────| GW=192.168.10.2 / DNS=192.168.10.2
   |─── Request ────►|
   |◄── ACK ─────────| IP asignada, GW=192.168.10.2

Resultado: el cliente configura gateway y DNS falsos.
           Todo su tráfico pasa a través de Kali.
```

### Estructura del paquete DHCP Offer / ACK

```text
[Ether]   src=MAC_atacante   dst=ff:ff:ff:ff:ff:ff
  [IP]    src=192.168.10.2   dst=255.255.255.255
    [UDP] sport=67           dport=68
      [BOOTP] op=2           yiaddr=IP_asignada   siaddr=192.168.10.2
        [DHCP] options:
          message-type : offer / ack
          server_id    : 192.168.10.2
          lease_time   : 3600
          subnet_mask  : 255.255.255.0
          router       : 192.168.10.2
          name_server  : 192.168.10.2
```

---

## 🌐 Documentación de la Red

### Topología del Laboratorio

```text
+------------------+        +---------------------+        +---------------------+
|   Kali Linux     |        |        SW2          |        |        SW1          |
|   (Atacante)     |◄──────►|  GNS3 vIOS-L2       |◄──────►|  GNS3 vIOS-L2       |
|  eth0 / eth0.10  | Gi0/1  | VTP Client          | Gi0/0  | VTP Server          |
| 0c:bf:c5:c2:00:00|        | 0cc0.7fb8.0000      |        | 0cb5.a4d7.0000      |
+------------------+        +---------------------+        +---------------------+
                                                                    | Gi0/1
                                                         +---------------------+
                                                         |         R1          |
                                                         |  192.168.10.1/24    |
                                                         +---------------------+
```

> Topología completa disponible en `Topologia/Topologia.png`

### Tabla de Direccionamiento

| Dispositivo | Interfaz | VLAN | IP / Máscara | MAC | Rol |
|---|---|---|---|---|---|
| Kali Linux | `eth0.10` | 10 | 192.168.10.2/24 | `0c:bf:c5:c2:00:00` | Atacante / servidor rogue |
| SW1 | Gi0/0 (trunk) | 1, 10 | — | `0cb5.a4d7.0000` | VTP Server / Root Bridge |
| SW2 | Gi0/1 (acceso) | 1, 10 | — | `0cc0.7fb8.0000` | VTP Client |
| R1 | Gi0/0 | 10 | 192.168.10.1/24 | — | Gateway / DHCP Server legítimo |

```text
VTP Domain  : EGALDITO_LAB
SW1         : VTP Server | STP Root Bridge | Priority 32769 | MAC 0cb5.a4d7.0000
SW2         : VTP Client
VLAN 10     : RED_LOCAL — 192.168.10.0/24
```

---

## 🛡️ Contramedidas

El archivo de mitigación está en `Mitigacion/Mitigacion-DHCP-Spoofing.ios`.

### 1. DHCP Snooping — defensa principal

```cisco
en
conf term
ip dhcp snooping
ip dhcp snooping vlan 10

! Puerto hacia el servidor DHCP legítimo (R1) = trusted
interface GigabitEthernet0/0
 ip dhcp snooping trust
exit

! Puerto del atacante = untrusted (por defecto)
! Limitar tasa de paquetes DHCP
interface GigabitEthernet0/1
 ip dhcp snooping limit rate 10
exit
do wr
```

> DHCP Snooping bloquea los DHCP Offers provenientes de puertos untrusted, impidiendo que el servidor rogue entregue configuraciones falsas a los clientes. Solo el puerto marcado como `trust` (hacia R1) puede enviar respuestas DHCP.
>
> **Nota:** La mitigación se aplica sobre `vlan 10` porque es la VLAN donde el script realiza el ataque (`eth0.10`). Aplicarla solo en VLAN 1 no protegería a los clientes de VLAN 10.

### 2. Port Security — defensa complementaria

```cisco
interface GigabitEthernet0/1
 switchport port-security
 switchport port-security maximum 3
 switchport port-security violation restrict
 switchport port-security mac-address sticky
```

### Verificación

```cisco
SW2# show ip dhcp snooping
SW2# show ip dhcp snooping binding
SW2# show ip dhcp snooping statistics
```

---

## 🎬 Video Demostrativo

**Lista de reproducción EGALDITO\_LAB — Layer 2 Network Attacks:**
[https://www.youtube.com/playlist?list=PL24FUvJVT9rBmlkIyA1pGp28VHhh3JK1j](https://www.youtube.com/playlist?list=PL24FUvJVT9rBmlkIyA1pGp28VHhh3JK1j)

**Video de este ataque:**
[https://youtu.be/i4Lo84_Ymf0](https://youtu.be/i4Lo84_Ymf0)

---

*Laboratorio desarrollado con fines estrictamente educativos en entorno GNS3 aislado.*
*Autor: Edgardy Olivero | 20250704 | EGALDITO\_LAB*
