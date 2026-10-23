# ABN — cópia local e área de fornecedores

Cópia das páginas públicas de https://abnequipamentos.com.br/, com HTML, CSS, imagens e scripts visuais armazenados em `mirror/`. O arquivo `mirror/report.json` registra a cobertura e eventuais falhas. Não inclui código PHP, banco de dados nem administração do WordPress original. Formulários de contato, rastreamento e integrações WordPress foram retirados da cópia. Links externos de redes sociais, telefone e e-mail continuam apontando para seus destinos originais.

Base em Django 5.2 LTS: autenticação, senhas com hash, proteção CSRF e administração já disponíveis. A interface pública preserva o site original; a área restrita é uma implementação inicial separada.

## Referência visual

Para consultar ou adaptar somente o visual da área de fornecedores, os principais arquivos são:

- `templates/base.html`: estrutura geral, cabeçalho, navegação e CSS da área;
- `templates/form.html`: telas de formulário e acesso;
- `templates/dashboard.html`: painel e tabela de avaliações;
- `templates/includes/site_footer.html`: rodapé;
- `mirror/`: HTML, CSS, imagens e demais recursos copiados do site institucional.

Os templates contêm marcações específicas do Django, mas podem ser usados como referência de layout e identidade visual em outra tecnologia.

## Executar no Windows / PowerShell

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python manage.py migrate
.venv\Scripts\python manage.py createsuperuser
.venv\Scripts\python manage.py runserver 0.0.0.0:8000
```

Neste computador, abra http://127.0.0.1:8000/. Em outros computadores da mesma rede, abra http://192.168.0.80:8000/. Administração: `/admin/`. Portal: `/fornecedores/`. Importação: `/admin/suppliers/evaluation/importar/`.

## Cadastrar fornecedor

```powershell
.venv\Scripts\python manage.py create_supplier --email compras@fornecedor.com.br --cnpj 11111111111111 --name "Fornecedor de teste"
```

A senha é solicitada no terminal e não aparece nos argumentos. O CNPJ do exemplo é fictício. O CNPJ passa a ser o login permanente da empresa; o e-mail fica apenas como contato e pode ser alterado sem afetar o acesso. A validação atual verifica formato e unicidade, não consulta cadastro fiscal. O comando cria usuário comum e vínculo exclusivo com um fornecedor. Não existe cadastro público. Alternativamente, no admin crie usuário com **nome de usuário igual ao CNPJ com 14 dígitos**, sem permissões de equipe/superusuário, e associe-o ao fornecedor. Cada conta corresponde a um fornecedor.

O fornecedor entra com CNPJ e senha, pode trocar a senha autenticado e usar **Esqueci minha senha**, informando o CNPJ. O endereço de recuperação é o e-mail mantido no cadastro do fornecedor e sincronizado com a conta de acesso. Durante a fase de testes, nenhum e-mail é enviado.

Na lista de fornecedores do admin, use **Criar senha temporária** ou **Resetar senha**. A senha é enviada ao e-mail cadastrado e também exibida uma única vez ao administrador. Durante a etapa de testes, não é exigida a troca no primeiro acesso.

## Importar notas

O administrador envia os resultados em `/admin/suppliers/evaluation/importar/`, acessível em **Avaliações → Importar CSV**. A página também oferece o download do arquivo de exemplo. Envie CSV UTF-8 (BOM opcional), separado por vírgula ou ponto e vírgula, com cabeçalho `cnpj,razaosocial,nota`. `exemplo-avaliacoes.csv` demonstra o formato. O exercício é o ano atual. A nota é um texto, como `A`, `B` ou `C`.

O CNPJ é validado pelos dígitos verificadores. Quando ele ainda não existe, o fornecedor e seu usuário são criados automaticamente com a senha de testes `abn@2026`, sem troca obrigatória no primeiro acesso. O CNPJ identifica o fornecedor e uma nova importação pode atualizar sua razão social. Nota vazia ou contendo erro `DIV/0` é armazenada como “Sem nota”.

A importação aceita até 2 MB / 10.000 linhas, rejeita duplicidades no arquivo e desfaz todas as alterações se qualquer linha for inválida. Reimportar o mesmo CNPJ e exercício atualiza a nota existente.

Todas as consultas do portal filtram pelo usuário da sessão no servidor. Não há listagem, busca ou rota pública de outros fornecedores. Parâmetros de CNPJ/ID enviados pelo navegador não alteram esse filtro. Respostas de avaliações não podem ser armazenadas em cache. Somente administradores autorizados devem receber acesso de equipe/superusuário.

## Verificação e atualização da cópia

```powershell
.venv\Scripts\python manage.py test
.venv\Scripts\python scripts/copy_site.py
```

O segundo comando substitui os snapshots locais com uma nova leitura pública do site; preserve edições locais antes de executá-lo.

## Antes de disponibilizar na internet

Este projeto está configurado para testes locais com SQLite e DEBUG. Para produção: configurar `DJANGO_DEBUG=0`, segredo próprio em `DJANGO_SECRET_KEY`, hosts em `DJANGO_ALLOWED_HOSTS`, servidor WSGI e HTTPS; servir os arquivos estáticos coletados com `collectstatic`; adotar banco com backups, limitação de tentativas de login, auditoria de importações/acessos e recuperação de senha com e-mail. Validar regras de nota e CNPJ e revisar segurança antes de inserir dados reais. Não há publicação nem alteração do site original.

Para habilitar o envio real, configure `PASSWORD_RECOVERY_EMAIL_ENABLED=1`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` e `DEFAULT_FROM_EMAIL`. Por padrão, `PASSWORD_RECOVERY_EMAIL_ENABLED=0` impede qualquer envio durante os testes.

Referência da autenticação: https://docs.djangoproject.com/en/5.2/topics/auth/default/.
