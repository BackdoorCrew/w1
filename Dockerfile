# Dockerfile na pasta D:\hackaton\w1\w1\

# imagem base com Python e Linux leve
FROM python:3.11-slim

# define diretório de trabalho dentro do container
WORKDIR /app

# copia só requirements para instalar dependências
COPY requirements.txt .

# instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# copia todo o seu código Django
COPY . .

# expõe a porta padrão do Django dev server
EXPOSE 8000

# comando padrão para subir o servidor
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
