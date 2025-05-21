# docker_entrypoint.py
import os
import subprocess
import sys
import time

def execute_command(cmd_list, step_name, exit_on_error=True, working_directory=None):
    """
    Executa um comando e lida com o resultado, imprimindo stdout/stderr.
    """
    final_cmd_list = [str(c) for c in cmd_list] # Garante que todos os args são strings
    print(f"INFO: Executando {step_name}: {' '.join(final_cmd_list)}")
    try:
        # Executa o comando. stdout e stderr do processo filho serão impressos no console do Docker.
        # Usar Popen para ter mais controle, mas run também funcionaria.
        process = subprocess.Popen(final_cmd_list, cwd=working_directory) 
        process.wait() # Espera o comando terminar

        if process.returncode != 0:
            print(f"ERRO: Falha ao executar {step_name} (código de saída: {process.returncode}).", file=sys.stderr)
            if exit_on_error:
                sys.exit(process.returncode)
            return False # Indica falha
        print(f"INFO: {step_name} executado com sucesso.")
        return True # Indica sucesso
    except FileNotFoundError:
        print(f"ERRO: Comando '{final_cmd_list[0]}' não encontrado. Verifique o PATH e a existência do arquivo.", file=sys.stderr)
        if exit_on_error:
            sys.exit(1)
        return False
    except Exception as e:
        print(f"ERRO: Erro inesperado ao executar {step_name}: {e}", file=sys.stderr)
        if exit_on_error:
            sys.exit(1)
        return False

if __name__ == "__main__":
    print("INFO: Iniciando entrypoint Python (docker_entrypoint.py)...")
    
    # O WORKDIR /app já está definido no Dockerfile, então os comandos devem encontrar manage.py
    # e create_dev_admin.py se estiverem na raiz do /app.

    # 1. Aplicar migrações do banco de dados.
    # A condição 'service_healthy' no docker-compose.yml para o serviço 'db'
    # deve garantir que o banco de dados esteja pronto antes que este contêiner inicie
    # completamente e execute este script.
    execute_command(
        ['python', 'manage.py', 'migrate', '--noinput'],
        step_name="migrações do banco de dados"
    )

    # 2. Executar o script para criar o superusuário de desenvolvimento.
    # O script create_dev_admin.py já verifica se o usuário existe, então é seguro executá-lo.
    # Não sair em caso de erro aqui, pois o script create_dev_admin pode apenas avisar que o usuário já existe.
    execute_command(
        ['python', 'create_dev_admin.py'],
        step_name="criação/verificação de superusuário",
        exit_on_error=False 
    )
    
    # 3. (Opcional) Coletar arquivos estáticos.
    # Você pode controlar isso com uma variável de ambiente se desejar.
    # Exemplo: if os.environ.get('DJANGO_COLLECTSTATIC') == 'true':
    # execute_command(
    # ['python', 'manage.py', 'collectstatic', '--noinput', '--clear'],
    # step_name="coleta de arquivos estáticos"
    # )

    # 4. Executar o comando principal que foi passado para o container
    # (originalmente definido pelo CMD no Dockerfile).
    # sys.argv[0] é o nome do script (docker_entrypoint.py).
    # sys.argv[1:] são os argumentos passados após o nome do script.
    # Estes argumentos vêm do CMD do Dockerfile.
    main_command_args = sys.argv[1:] 
    
    if main_command_args:
        print(f"INFO: Executando comando principal: {' '.join(main_command_args)}")
        try:
            # os.execvp substitui o processo atual (o script Python) pelo novo comando.
            # Isso é importante para que o processo do servidor Django (ou Gunicorn/Uvicorn em produção)
            # se torne o processo principal (PID 1) no container, se possível, ou pelo menos
            # receba sinais do Docker (como SIGTERM para um shutdown gracioso) corretamente.
            os.execvp(main_command_args[0], main_command_args)
        except FileNotFoundError:
            print(f"ERRO: Comando principal '{main_command_args[0]}' não encontrado.", file=sys.stderr)
            sys.exit(127) # Código de saída comum para "comando não encontrado"
        except Exception as e:
            print(f"ERRO: Falha ao tentar executar o comando principal '{' '.join(main_command_args)}': {e}", file=sys.stderr)
            sys.exit(1) # Código de erro genérico
    else:
        print("ERRO: Nenhum comando principal (CMD) especificado no Dockerfile para o entrypoint executar.", file=sys.stderr)
        print("INFO: Por favor, defina um CMD no seu Dockerfile, como por exemplo:", file=sys.stderr)
        print("INFO: CMD [\"python\", \"manage.py\", \"runserver\", \"0.0.0.0:8000\"]", file=sys.stderr)
        sys.exit(1) # Sai com erro se nenhum CMD for fornecido.