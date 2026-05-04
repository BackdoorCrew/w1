(https://w1-production-f1be.up.railway.app/)
tinha feito deploy, mas acabou os créditos

FEITO POR:
Guilherme Beccato Stern
Diogo Musso Coutinho
# Plataforma de Gestão de Holdings W1

Este projeto é uma plataforma web desenvolvida para facilitar a criação, gestão e acompanhamento de Holdings patrimoniais. O sistema visa oferecer ferramentas para otimizar o planejamento sucessório, proteger o patrimônio e melhorar a gestão financeira dos usuários.

## Tecnologias Utilizadas

* **Backend:** Python com Django Framework
* **Frontend:** HTML, CSS, JavaScript
* **Banco de Dados:** PostgreSQL
* **Containerização:** Docker e Docker Compose
* **Comunicação Externa:** Integração com Z-API para notificações via WhatsApp.
* **Inteligência Artificial:** Uso da API da OpenAI para funcionalidades de chat inteligente.
* **Autenticação:** Django Allauth com suporte a login social (Google).
* **Servidor de Arquivos Estáticos (Produção):** Whitenoise

## Principais Funcionalidades

* **🤖 Inteligência Artificial:** Assistente virtual (via API OpenAI) integrado ao chat para auxiliar os usuários com dúvidas e informações sobre holdings.
* **📱 Integração com WhatsApp:** Notificações automáticas (via Z-API) para clientes e consultores sobre:
    * Novos documentos adicionados ao processo da holding.
    * Mudanças de status no processo da holding.
    * Novas mensagens no chat da holding.
* **📂 Gestão de Documentos:**
    * Upload de documentos por clientes e consultores.
    * Organização de documentos em pastas e subpastas dentro de cada processo de holding.
    * Versionamento automático de documentos com o mesmo nome lógico.
* **💬 Grupos de Mensagens por Holding:**
    * Espaço de chat dedicado para cada holding, permitindo comunicação entre sócios (clientes) e consultores.
    * Acessível tanto pelo portal do cliente quanto pelo portal de gestão (administradores/consultores).
* **📊 Acompanhamento de Progresso:**
    * Visualização do status atual do processo de criação e oficialização da holding (ex: "Aguardando Documentos", "Documentação em Análise", "Concluído").
* **👥 Gestão de Sócios (Clientes) e Consultores:**
    * Diferentes tipos de usuários (Cliente, Consultor, Admin).
    * Associação de múltiplos clientes (sócios) e consultores a uma holding.
* **⚙️ Portal de Administração e Consultoria (Management):**
    * Dashboard com visão geral do sistema (total de usuários, holdings, processos recentes).
    * Busca global por usuários e holdings.
    * Listagem e detalhamento de usuários e holdings.
    * Gerenciamento de clientes e consultores associados a cada holding.
    * Visualização e envio de mensagens no chat de cada holding.
    * Criação de novos consultores.
    * Acesso e gestão de documentos e pastas dos processos.
* **💡 Simulação de Economia:** Ferramenta para usuários simularem os benefícios financeiros (economia de impostos, custos de inventário, etc.) ao optar por uma holding.
* **🔑 Autenticação Segura:** Login com e-mail/senha e opção de login social utilizando contas Google, gerenciado pelo Django Allauth.
* **📝 Criação de Holding Simplificada:** Fluxo para o cliente manifestar interesse e iniciar o processo de criação de uma holding.

## Como Rodar Localmente

1.  **Pré-requisitos:**
    * Docker Desktop instalado e em execução.
    * Git (para clonar o repositório).

2.  **Configuração Inicial:**
    * Clone este repositório para sua máquina local.
    * Na raiz do projeto, crie um arquivo chamado `.env`. Este arquivo armazenará suas variáveis de ambiente. Baseie-se no arquivo `w1/settings.py` para saber quais variáveis são esperadas (ex: `SECRET_KEY`, `DEBUG`, `DATABASE_URL`, `OPENAI_API_KEY`, `ZAPI_INSTANCE_ID`, `ZAPI_CLIENT_TOKEN`, `ZAPI_SECURITY_TOKEN`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, etc.).
        *Exemplo de `.env` básico:*
        ```env
        SECRET_KEY=sua_secret_key_super_segura
        DEBUG=True
        ALLOWED_HOSTS=localhost,127.0.0.1
        DATABASE_URL=postgres://testuser:testpassword@db:5432/testdb
        # Adicione outras chaves de API e configurações conforme necessário
        OPENAI_API_KEY=sk-xxxxxxxxxxxx
        ZAPI_INSTANCE_ID=xxxxxxxxxxxx
        ZAPI_CLIENT_TOKEN=xxxxxxxxxxxx
        ZAPI_SECURITY_TOKEN=xxxxxxxxxxxx  # Token de segurança da conta Z-API
        GOOGLE_CLIENT_ID=seu_google_client_id.apps.googleusercontent.com
        GOOGLE_CLIENT_SECRET=seu_google_client_secret
        DJANGO_SUPERUSER_EMAIL=admin@example.com
        DJANGO_SUPERUSER_PASSWORD=adminpass
        ```

3.  **Execução com Docker Compose:**
    * Abra um terminal na pasta raiz do projeto.
    * Execute o comando para construir as imagens e iniciar os contêineres em modo detached (`-d`):
        ```bash
        docker-compose up -d --build
        ```
    * Aguarde a conclusão da build e o início dos serviços. O `docker_entrypoint.py` tentará aplicar as migrações e criar um superusuário padrão automaticamente. Se precisar aplicar migrações manualmente ou se o entrypoint falhar por algum motivo no primeiro `up`, você pode usar:
        ```bash
        docker-compose exec web python manage.py migrate
        ```

4.  **Acesso à Aplicação:**
    * A plataforma estará acessível em: `http://localhost:8000/`
    * O painel administrativo do Django estará em: `http://localhost:8000/admin/`
        * As credenciais do superusuário padrão são definidas pelas variáveis `DJANGO_SUPERUSER_EMAIL` e `DJANGO_SUPERUSER_PASSWORD` no seu arquivo `.env` (ou pelos defaults em `create_dev_admin.py` caso as variáveis não sejam definidas).

https://w1-production-f1be.up.railway.app/ (parou de funcionar pois paramos de pagar)
Para acessar a página de editar holding, clica em cima do nome da holding, tendo feito login com o superadmin

