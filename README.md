Detector de Hosts ICMP

Este script em Python é uma ferramenta de linha de comando para detectar hosts ativos na rede usando o protocolo ICMP (Internet Control Message Protocol), com a opção de especificar uma máscara de rede. O script envia pacotes ICMP echo request (ping) para uma lista de endereços IP na rede especificada e aguarda por respostas para determinar quais hosts estão ativos.

Funcionalidades:
Envio de Pacotes ICMP: O script envia pacotes ICMP echo request para uma lista de endereços IP na rede especificada.
Detecção de Hosts Ativos: Ele espera por respostas dos hosts e identifica quais estão ativos na rede.
Opção de Máscara de Rede: Permite especificar uma máscara de rede para determinar o escopo da detecção de hosts.

Requisitos:
Python 3.x
Pacote pyfiglet para exibir o banner (instalado automaticamente via pip, se necessário)
Uso:
./hicmp.py -d <domínio ou domínios> -w <tempo de espera> -o <arquivo de saída>

	-d, --domain: Especifica o domínio ou domínios a serem verificados. Pode ser um único endereço IP ou uma faixa de endereços IP. Obrigatório.
	-w, --wait: Especifica o tempo de espera entre os pacotes ICMP enviados, em segundos. O padrão é 0.0001 segundos.
	-o, --output: Especifica o nome do arquivo de saída para salvar os hosts encontrados. O padrão é output.txt.

Exemplo de Uso:
./hicmp.py -d 192.168.0.0/24 -w 0.0001 -o hosts_encontrados.txt

Este comando irá verificar todos os hosts na sub-rede 192.168.0.0/24, com um intervalo de espera de 0.0001 segundos entre os pacotes ICMP enviados, e salvará os IPs encontrados no arquivo hosts_encontrados.txt.
Notas:

É recomendado executar o script com privilégios de superusuário (root) para garantir acesso aos sockets raw necessários para enviar e receber pacotes ICMP.

Este script é destinado apenas para fins educacionais ou de diagnóstico. O uso indevido pode violar políticas de rede ou leis de privacidade.
