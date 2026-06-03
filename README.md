![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python) ![Scapy](https://img.shields.io/badge/Scapy-2.x-green) ![GNS3](https://img.shields.io/badge/GNS3-vIOS--L2-orange) ![Lab](https://img.shields.io/badge/Lab-EGALDITO__LAB-red)

# DHCP Spoofing Attack

> **Autor:** Edgardy Olivero | **Matricula:** 20250704  
> **Laboratorio:** EGALDITO_LAB | **Herramienta:** Python 3 + Scapy  
> **Repositorio:** [github.com/Edgardy715/DHCP-spoofing](https://github.com/Edgardy715/DHCP-spoofing)

---

## Objetivo del Laboratorio

Demostrar como un atacante puede desplegar un servidor DHCP fraudulento que responda antes que el servidor legitimo, asignando a los clientes una puerta de enlace y DNS falsos controlados por el atacante. El resultado es una posicion de Man-in-the-Middle pasiva sobre el trafico de los nuevos clientes DHCP [web:46][web:53][web:57].

## Objetivo del Script

Escuchar solicitudes DHCP Discover en VLAN10, responder con DHCP Offer y ACK que asignan la IP del atacante como gateway y DNS, completar el handshake DORA completo y mantener un pool de IPs falsas asignadas por MAC de cliente. El script actua como un servidor DHCP rogue en la red y contesta a los clientes antes que el servidor legitimo [web:52][web:54][web:57].

---

## Estructura del Repositorio

```text
DHCP-spoofing/
├── Script/
│   └── DHCP-Spoofing.py                  <- Script principal del ataque
├── Mitigacion/
│   └── Mitigacion-DHCP-Spoofing.ios      <- Comandos DHCP Snooping (Cisco IOS)
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

## Parametros del Script

| Variable | Valor | Descripcion |
|---|---|---|
| `IFACE` | `eth0.10` | Subinterfaz VLAN10 del atacante. |
| `FAKE_GW` | `192.168.10.2` | IP falsa anunciada como gateway, equivalente a la IP del atacante. |
| `FAKE_DNS` | `192.168.10.2` | IP falsa anunciada como servidor DNS. |
| `SUBNET` | `255.255.255.0` | Mascara de subred asignada. |
| `POOL` | `192.168.10.100-149` | Rango de IPs que entrega el servidor falso. |
| `lease_time` | `3600` | Duracion de la concesion en segundos (1 hora). |
| `asignado` | dict `{mac: ip}` | Registro de IPs entregadas por MAC cliente. |

---

## Requisitos

```bash
# Dependencias
pip install scapy

# Configurar subinterfaz VLAN10
ip link add link eth0 name eth0.10 type vlan id 10
ip link set eth0.10 up

# Asignar IP al atacante en VLAN10
ip addr add 192.168.10.2/24 dev eth0.10

# Ejecutar como root
sudo python3 Script/DHCP-Spoofing.py
```

---

## Funcionamiento del Script

### Flujo de ejecucion

```text
1. Verifica privilegios root.
2. sniff() escucha en eth0.10 filtrando udp port 67.
3. dhcp_handler() procesa cada paquete:
   |-- DHCP Discover (tipo 1):
   |   -> asigna una IP del POOL a la MAC del cliente.
   |   -> envia DHCP Offer con FAKE_GW y FAKE_DNS.
   '-- DHCP Request (tipo 3):
       -> recupera la IP asignada.
       -> envia DHCP ACK confirmando la concesion.
4. Ctrl+C -> cleanup(): imprime total de IPs asignadas.
```

### Intercambio DORA modificado

```text
Cliente              Atacante (servidor falso)         R1 (servidor legitimo)
   |--- Discover --->|
   |                 |--- Discover --->                 | (llega tarde o es ignorado)
   |<-- Offer -------|  GW=192.168.10.2 / DNS=192.168.10.2
   |--- Request ---->|
   |<-- ACK ---------|  IP asignada, GW=192.168.10.2

Resultado: el cliente configura gateway y DNS falsos, y su trafico pasa por Kali.
```

### Estructura del paquete DHCP Offer/ACK

```text
[Ether]   src=MAC_atacante  dst=ff:ff:ff:ff:ff:ff
  [IP]    src=192.168.10.2  dst=255.255.255.255
    [UDP] sport=67          dport=68
      [BOOTP] op=2          yiaddr=IP_asignada  siaddr=192.168.10.2
        [DHCP] options:
          message-type: offer / ack
          server_id:    192.168.10.2
          lease_time:   3600
          subnet_mask:  255.255.255.0
          router:       192.168.10.2
          name_server:  192.168.10.2
```

---

## Documentacion de la Red

### Topologia del Laboratorio

```text
+------------------+        +---------------------+        +---------------------+
|   Kali Linux     |        |        SW2          |        |        SW1          |
|   (Atacante)     |<------>|  GNS3 vIOS-L2       |<------>|  GNS3 vIOS-L2      |
|  eth0 / eth0.10  |  Gi0/1 | VTP Client          |  Gi0/0 | VTP Server         |
| 0c:bf:c5:c2:0000 |        | 0cc0.7fb8.0000      |        | 0cb5.a4d7.0000    |
+------------------+        +---------------------+        +---------------------+
                                                                   |  Gi0/1
                                                        +---------------------+
                                                        |         R1          |
                                                        |  192.168.10.1/24    |
                                                        +---------------------+
```

> Topologia completa en `Topologia/Topologia.png`

### Tabla de Direccionamiento

| Dispositivo | Interfaz | VLAN | IP / Mascara | MAC | Rol |
|---|---|---|---|---|---|
| Kali Linux | eth0.10 | 10 | 192.168.10.2/24 | `0c:bf:c5:c2:00:00` | Atacante / servidor rogue |
| SW1 | Gi0/0 (trunk) | 1,10 | — | `0cb5.a4d7.0000` | VTP Server / Root |
| SW2 | Gi0/0 (trunk) | 1,10 | — | `0cc0.7fb8.0000` | VTP Client |
| R1 | Gi0/0 | 10 | 192.168.10.1/24 | — | Gateway / DHCP legitimo |

```text
VTP Domain: EGALDITO_LAB | SW1: VTP Server | SW2: VTP Client
STP Root Bridge: SW1 | Priority: 32769 | MAC: 0cb5.a4d7.0000
VLAN 10: RED_LOCAL (192.168.10.0/24)
```

---

## Capturas de Pantalla

| Momento | Descripcion |
|---|---|
| Pre-ataque | Cliente obtiene IP con GW=192.168.10.1 (R1 legitimo). |
| Durante ataque | El script imprime `[DISCOVER] mac -> Ofreciendo IP GW=192.168.10.2`. |
| Efecto | `ip route` del cliente muestra default via 192.168.10.2. |
| Verificacion | Trafico del cliente pasa por Kali y puede capturarse con Wireshark. |

---

## Contramedidas

El archivo de mitigacion esta en `Mitigacion/Mitigacion-DHCP-Spoofing.ios`.

### 1. DHCP Snooping — defensa principal

```cisco
en
conf term
! Habilitar DHCP Snooping globalmente
ip dhcp snooping
! Aplicar a la VLAN correspondiente
ip dhcp snooping vlan 1

! Puerto hacia el servidor DHCP legitimo (R1) = trusted
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

> DHCP Snooping bloquea los DHCP Offers provenientes de puertos untrusted y mantiene una base de bindings para saber que IP, MAC y puerto corresponden a cada host [web:52][web:54][web:55][web:57].

### Verificacion

```cisco
SW2# show ip dhcp snooping
SW2# show ip dhcp snooping binding
SW2# show ip dhcp snooping statistics
```

### 2. Port Security para limitar MACs por puerto

```cisco
interface GigabitEthernet0/1
 switchport port-security
 switchport port-security maximum 3
 switchport port-security violation restrict
 switchport port-security mac-address sticky
```

---

## Video Demostrativo

**Lista de reproduccion EGALDITO_LAB:** [Layer 2 Network Attacks](https://www.youtube.com/@Edgardy715)

---

*Laboratorio desarrollado con fines estrictamente educativos en entorno GNS3 aislado.*  
*Autor: Edgardy Olivero | 20250704 | EGALDITO_LAB*
