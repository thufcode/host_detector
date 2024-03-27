#!/bin/python3
# Author: Romildo Santos
# importações
import socket, struct, ipaddress, time, random, argparse
import pyfiglet

banner = pyfiglet.figlet_format("HOST DETECTOR")
print(banner)

SIGNAL = True
#entrada de dados pelo terminal
parser = argparse.ArgumentParser(description='Um detector de hosts em icmp com opção de mascara de rede em python', usage='./hicmp.py -d 192.168.0.0/16 -w 0.0001 -o dominios.txt')
parser.add_argument('-d', '--domain', action='store', dest='hosts', help='dominio ou dominios', required=True)
parser.add_argument('-o', '--output', action='store', dest='output', default='output.txt', help='salvar em um arquivo os hosts encontrados')
parser.add_argument('-w', '--wait', action='store', dest='wait', default='0.0001', help='tempo de espera', type=float)
arguments = parser.parse_args()

#calculo para criar o pacote icmp
def checksum(source_string):
    sum = 0
    count_to = (len(source_string) / 2) * 2
    count = 0
    while count < count_to:
        this_val = source_string[count + 1] * 256 + source_string[count]
        sum = sum + this_val
        sum = sum & 0xffffffff
        count = count + 2
    if count_to < len(source_string):
        sum = sum + source_string[len(source_string) - 1]
        sum = sum & 0xffffffff
    sum = (sum >> 16) + (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

#criar pacote
def create_packet(id):
    header = struct.pack('bbHHh', 8, 0, 0, id, 1)
    data = 192 * 'Q'
    my_checksum = checksum(header + data.encode())
    header = struct.pack('bbHHh', 8, 0, socket.htons(my_checksum), id, 1)
    return header + data.encode()

#definindo o ping(requisição icmp)
def ping(addr, timeout=1):
    try:
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        packet_id = int((id(timeout) * random.random()) % 65535)
        packet = create_packet(packet_id)
        my_socket.connect_ex((addr, 80))
        my_socket.sendall(packet)
        my_socket.close()
    except PermissionError:
        print('[*] Este programa precisa ser iniciado como root')
    except Exception as e:
        print(e)

#enviando os pacotes icmp e salvando
def rotate(addr, file_name, wait, responses):
    print("[*] Enviando pacotes  \n")
    for ip in addr:
        ping(str(ip))
        time.sleep(wait)

    print("[*] Todos os pacotes foram enviados\n")

    print("[*] Esperando por todas as respostas\n")
    time.sleep(2)

    # Parando de esperar
    global SIGNAL
    SIGNAL = False
    ping('127.0.0.1')  # ping falso para parar de esperar

    print(len(responses), "-> Hosts enconctrados\n")
    hosts = []
    if len(arguments.output) > 0:
        file = open(file_name, 'w')
        i = 0
        for response in sorted(responses):
            i += 1
            ip = struct.unpack('BBBB', response)
            ip = f'{ip[0]}.{ip[1]}.{ip[2]}.{ip[3]}'
            hosts.append(ip)
            file.write(f'Host{i}: ' + str(ip) + '\n')
        print('[*] Escrevendo arquivo...\n')
    print("[*] Processo encerrado\n")
    print(f'[*] Horario de encerramento: {time.strftime("%H:%M:%S")}')
    print(Fore.RESET + '-' * 65)


def listener(responses, ip_network):
    global SIGNAL
    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    s.bind(('', 1))
    print(f'[*] Horario de inicio: {time.strftime("%H:%M:%S")}\n')
    print("[*] Listando")
    print('')
    while SIGNAL:
        packet = s.recv(1024)[:20][-8:-4]
        if packet not in responses and ipaddress.ip_address(packet) in ip_network:
            responses.append(packet)
    print("[*] Fim do listamento\n")
    s.close()

def main():
    responses = []

    ips = arguments.hosts

    wait = arguments.wait
    file_name = arguments.output

    ip_network = ipaddress.ip_network(ips, strict=False)

    t_server = Thread(target=listener, args=[responses, ip_network])
    t_ping = Thread(target=rotate, args=[ip_network, file_name, wait, responses])
    t_server.start()
    t_ping.start()
if __name__ == '__main__':
    main()

