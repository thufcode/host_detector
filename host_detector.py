import socket
import struct
import ipaddress
import time
import random
from concurrent.futures import ThreadPoolExecutor
from threading import Event
import argparse
import os
import pyfiglet
from tqdm import tqdm
import logging
import signal

# Configurando logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Banner do script
banner = pyfiglet.figlet_format("HOST DETECTOR")
print(banner)

# Sinal para controle de threads
STOP_SIGNAL = Event()

# Validacao de permissao
if os.geteuid() != 0:
    logger.error("Este script precisa ser executado como root.")
    exit(1)

# Entrada de dados pelo terminal
parser = argparse.ArgumentParser(description='Detector de hosts usando ICMP',
                                 usage='./hicmp.py -d 192.168.0.0/16 -w 0.1 -o dominios.txt')
parser.add_argument('-d', '--domain', required=True, help='Domínio ou range de IPs (ex.: 192.168.0.0/24)')
parser.add_argument('-o', '--output', default='output.txt', help='Arquivo para salvar os hosts encontrados')
parser.add_argument('-w', '--wait', default=0.1, type=float, help='Intervalo entre os pings em segundos')
parser.add_argument('--verbose', action='store_true', help='Exibe logs detalhados')
arguments = parser.parse_args()

if arguments.verbose:
    logger.setLevel(logging.DEBUG)

# Calculo do checksum
def checksum(source_string):
    sum = 0
    count_to = (len(source_string) // 2) * 2
    count = 0
    while count < count_to:
        this_val = source_string[count + 1] * 256 + source_string[count]
        sum += this_val
        sum &= 0xffffffff
        count += 2
    if count_to < len(source_string):
        sum += source_string[-1]
        sum &= 0xffffffff
    sum = (sum >> 16) + (sum & 0xffff)
    sum += (sum >> 16)
    return ~sum & 0xffff

# Criar pacote ICMP
def create_packet(id):
    header = struct.pack('bbHHh', 8, 0, 0, id, 1)
    data = 192 * 'Q'
    my_checksum = checksum(header + data.encode())
    header = struct.pack('bbHHh', 8, 0, socket.htons(my_checksum), id, 1)
    return header + data.encode()

# Definindo o ping (requisicao ICMP)
def ping(addr, timeout=1):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as my_socket:
            packet_id = int((id(timeout) * random.random()) % 65535)
            packet = create_packet(packet_id)
            my_socket.settimeout(timeout)
            my_socket.sendto(packet, (addr, 1))
            logger.debug(f"Ping enviado para {addr}")
    except socket.timeout:
        pass
    except Exception as e:
        logger.error(f"Erro ao enviar ping para {addr}: {e}")

# Escutando respostas ICMP
def listener(responses, ip_network):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as s:
            s.bind(('', 1))
            logger.info("Escutando respostas ICMP")
            while not STOP_SIGNAL.is_set():
                try:
                    packet, addr = s.recvfrom(1024)
                    ip = addr[0]
                    if ip not in responses and ipaddress.ip_address(ip) in ip_network:
                        responses.add(ip)
                        logger.debug(f"Resposta recebida de {ip}")
                except socket.timeout:
                    continue
    except Exception as e:
        logger.error(f"Erro no listener: {e}")

# Enviando pacotes ICMP e salvando os resultados
def rotate(addr, file_name, wait, responses):
    logger.info("Enviando pacotes ICMP")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(ping, str(ip)) for ip in tqdm(addr, desc="Pingando hosts")]
        for future in futures:
            if STOP_SIGNAL.is_set():
                break
            time.sleep(wait)

    logger.info("Todos os pacotes foram enviados")
    STOP_SIGNAL.set()

    logger.info(f"{len(responses)} hosts encontrados")
    with open(file_name, 'w') as file:
        for i, ip in enumerate(sorted(responses), start=1):
            file.write(f'Host {i}: {ip}\n')
    logger.info(f"Resultados salvos em {file_name}")

# Finalizacao com sinal
responses = set()
def handle_exit(signum, frame):
    STOP_SIGNAL.set()
    logger.warning("Execução interrompida pelo usuário. Salvando resultados parciais...")
    with open(arguments.output, 'w') as file:
        for i, ip in enumerate(sorted(responses), start=1):
            file.write(f'Host {i}: {ip}\n')
    logger.info("Resultados parciais salvos. Saindo.")
    exit(0)

signal.signal(signal.SIGINT, handle_exit)

# Funcao principal
def main():
    try:
        ip_network = ipaddress.ip_network(arguments.domain, strict=False)
    except ValueError as e:
        logger.error(f"Domínio ou range de IPs inválido: {e}")
        exit(1)

    logger.info(f"Iniciando varredura em {arguments.domain}")

    t_server = Thread(target=listener, args=(responses, ip_network))
    t_server.start()

    rotate(ip_network, arguments.output, arguments.wait, responses)

    t_server.join()

    logger.info("Processo encerrado")

if __name__ == '__main__':
    main()
