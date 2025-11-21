
CONTRIBUTING
============

Obrigado por querer contribuir com o Treinaí! Este documento descreve passo a passo como preparar o ambiente de desenvolvimento, executar testes, seguir convenções de código e submeter contribuições.

Sumário
-------
- Requisitos
- Preparando o ambiente (Windows)
- Rodando o projeto localmente
- Executando testes (unitários e E2E)
- Estilo de código e lint
- Fluxo de contribuição (branch, commit, PR)
- Boas práticas para PRs
- Contato / dúvidas

Requisitos
----------
- Python 3.11 (ou compatível com o `requirements.txt`)
- Git
- Google Chrome (para testes E2E)
- ChromeDriver (pode ser gerenciado pelo `webdriver-manager`) — não é obrigatório instalar manualmente

Preparando o ambiente (Windows)
-------------------------------
1. Clone o repositório:

```powershell
git clone https://github.com/beatrizloyola/Projeto-FDS.git
cd Projeto-FDS
```

2. Crie e ative um virtualenv:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Atualize pip e instale dependências:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

4. (Opcional) Se for usar Selenium localmente, o projeto já usa `webdriver-manager` que baixa o ChromeDriver automaticamente. Se preferir gerenciar manualmente, instale a versão do ChromeDriver correspondente ao seu Chrome.

Configurações de ambiente úteis
------------------------------
- Para habilitar debug localmente (opcional):

```powershell
$env:DJANGO_DEBUG = 'True'
```

- Variáveis para Selenium remoto/CI:
	- `SELENIUM_REMOTE_URL` — URL do Selenium Grid/standalone chrome (opcional)
	- `SELENIUM_HOST_REWRITE` — host de reescrita para contêineres CI (opcional)
	- `CHROME_BIN` — caminho para binário do Chrome (quando necessário)

Rodando o projeto localmente
----------------------------
1. Crie o banco e aplique migrations locais (SQLite é o padrão):

```powershell
python manage.py migrate
```

2. Crie um superuser para o admin (opcional):

```powershell
python manage.py createsuperuser
```

3. Rode o servidor de desenvolvimento:

```powershell
python manage.py runserver
```

4. Acesse `http://127.0.0.1:8000/` para a aplicação. A área de login está na raiz.

Executando testes
-----------------
Unitários:

```powershell
python manage.py test
```

E2E (Selenium):

- Os testes E2E ficam em `e2e_tests/` e usam Chrome + `webdriver-manager`.
- Para rodar um teste específico:

```powershell
python manage.py test e2e_tests.test_historia7.Historia7E2ETests.test_cenario1_medalha_conquistada -v 2
```

- Em CI, você pode usar um Selenium Grid (defina `SELENIUM_REMOTE_URL`) ou rodar localmente com Chrome instalado.

Lint e estilo
-------------
- Siga as convenções de estilo do repositório: indentação de 4 espaços, nomes descritivos e evitar mudanças não relacionadas em PRs.
- Se quiser usar ferramentas, adicione/execute:

```powershell
pip install flake8 black
black .
flake8 .
```

Fluxo de contribuição
---------------------
1. Atualize seu fork / branch principal:

```powershell
git checkout main
git pull upstream main
```

2. Crie uma branch para sua feature/bugfix:

```powershell
git checkout -b feat/nome-curto-descritivo
```

3. Faça commits pequenos e atômicos com mensagens claras:

```powershell
git add <arquivos>
git commit -m "feat: adicionar X para resolver Y"
```

4. Rode testes localmente antes de abrir PR:

```powershell
python manage.py test
```

5. Push para seu fork e abra PR no repositório principal:

```powershell
git push origin feat/nome-curto-descritivo
```

Boas práticas para PRs
---------------------
- Descreva claramente o objetivo do PR e o problema que resolve.
- Vincule a issue (se existir) usando `#<número>` na descrição.
- Inclua passos para reproduzir/local testing quando relevante.
- Evite alterações de formatação em massa junto com mudanças funcionais.
- Atualize/adicione testes quando possível (unitários e/ou E2E).

Checklist antes de abrir PR
--------------------------
- Código compilando / rodando localmente
- Testes relevantes passando
- Mensagem de commit clara e branch descritiva
- Documentação atualizada (se necessário)

Problemas comuns e como debugar
------------------------------
- Erros E2E intermitentes:
	- Verifique se o Chrome está instalado e compatível com a versão do ChromeDriver.
	- Verifique variáveis de ambiente `CHROME_BIN`, `SELENIUM_REMOTE_URL` e `SELENIUM_HOST_REWRITE` se estiver em CI.
	- Aumente temporariamente timeouts em `e2e_tests` para debugar problemas de renderização.

- Migrações/DB:
	- Se houver erros relacionados a migrações, rode `python manage.py makemigrations` somente para alterações locais e cheque com o time antes de commitar migrations novas.

Contato / dúvidas
-----------------
Abra uma issue descrevendo seu problema ou sugira mudanças por PR. Para dúvidas rápidas, comente na issue relacionada ou no PR.

Agradecimentos
--------------
Obrigado por ajudar a melhorar o Treinaí! Sua contribuição é bem-vinda, pequenas melhorias e correções de bugs são tão valiosas quanto novas funcionalidades.

