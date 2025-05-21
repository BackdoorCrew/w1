# Dockerfile na pasta D:\hackaton\w1\w1\

# imagem base com Python e Linux leve
FROM python:3.11-slim

# define diretório de trabalho dentro do container
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# copia só requirements para instalar dependências
COPY requirements.txt .

# instala dependências
RUN pip install --no-cache-dir -r requirements.txt

COPY ./create_dev_admin.py /app/create_dev_admin.py
COPY ./docker_entrypoint.py /app/docker_entrypoint.py
RUN chmod +x /app/docker_entrypoint.py
# copia todo o seu código Django
COPY . .

# expõe a porta padrão do Django dev server
EXPOSE 8000
ENTRYPOINT ["python", "/app/docker_entrypoint.py"]

# comando padrão para subir o servidor
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
