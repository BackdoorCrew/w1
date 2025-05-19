#!/bin/sh

# Aguardar o banco de dados estar pronto (opcional, mas bom para robustez)
# Isso depende de como seu healthcheck do docker-compose está configurado.
# Se o 'depends_on' com 'service_healthy' já garante isso, pode não ser necessário aqui.
# echo "Aguardando PostgreSQL..."
# while ! nc -z db 5432; do # 'db' é o nome do seu serviço de banco no docker-compose.yml
#   sleep 0.1
# done
# echo "PostgreSQL iniciado"

echo "Aguardando PostgreSQL iniciar..."
# O nome 'db' deve corresponder ao nome do serviço do banco de dados no seu docker-compose.yml
# O 'nc' (netcat) pode não estar disponível na imagem python:3.11-slim por padrão.
# Se esta parte causar problemas, você pode removê-la ou instalar o netcat no Dockerfile.
# while ! nc -z db 5432; do
#   sleep 0.5
# done
# echo "PostgreSQL iniciado e pronto."

# Aplicar migrações do banco de dados
# É importante que as tabelas existam antes de tentar criar o superusuário.
echo "Aplicando migrações do banco de dados..."
python manage.py migrate --noinput

# Executar o script para criar o superusuário de desenvolvimento
# Este script verifica se o usuário já existe, então é seguro executá-lo sempre.
echo "Verificando/Criando superusuário de desenvolvimento..."
python create_dev_admin.py

# Coletar arquivos estáticos (opcional para desenvolvimento, mas bom para consistência com produção)
# echo "Coletando arquivos estáticos..."
# python manage.py collectstatic --noinput --clear

# Finalmente, executa o comando principal passado para o container
# (que será 'python manage.py runserver 0.0.0.0:8000' vindo do docker-compose.yml)
echo "Iniciando a aplicação Django..."
exec "$@"
