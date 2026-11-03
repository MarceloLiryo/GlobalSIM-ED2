# GlobalSIM — Serviço Internacional de Internet por eSIM (EDII)

Projeto prático da disciplina **Estruturas de Dados II** (Sistemas de Informação — UNEB, Profra. Maria Inés Restovic).

---

## Integrantes da Equipe
- Marcelo Líryo, Janderson Blanki

---

## Etapa 1: Tabela Hash e Aplicação Web

### 1. Estrutura Implementada (`HashTable`)
A classe `HashTable` (`app/models/hash_table.py`) foi implementada do zero utilizando **encadeamento externo (*separate chaining*)** para tratamento de colisões:
- **Chave**: Código internacional do país de 2 ou 3 letras normalizado em maiúsculas (`BR`, `PT`, `ES`, `FR`, `IT`, `US`, `CA`, `JP`).
- **Função de Espalhamento (`_hash_function`)**: Polinomial com base prima (`37`) ponderada pela posição do caractere, distribuindo chaves curtas de forma uniforme entre os *buckets*.
- **Instrumentação**: O sistema monitora e exibe na interface Web:
  - Capacidade da tabela ($M$), total de elementos ($N$) e Fator de Carga ($\alpha = N / M$).
  - Quantidade de *buckets* ocupados, colisões ativas e número de comparações na última busca.
  - Visualização gráfica de cada *bucket* e das listas encadeadas formadas em caso de colisão.

### 2. Arquitetura em Camadas e Persistência
- **`app/repository/country_repository.py`**: Único módulo que manipula o arquivo `app/data/countries.json` (usando `pathlib.Path` para compatibilidade entre Windows e Linux) e prepara exportação para `pandas.DataFrame`.
- **`app/models/country.py`**: Camada de negócio (`CountryModel`) que mantém a `HashTable` em memória durante a execução e aciona o repositório para persistir alterações.
- **`app/routes/home.py` e `app/routes/admin.py`**: Rotas Flask com templates Jinja2, formulários HTML e padrão **Post/Redirect/Get (PRG)**.

---

## Etapa 2: Árvore B e Gerenciamento de Clientes

**Entrega: 24/11/2026.**

### Objetivo
Ampliar o GlobalSIM para gerenciar clientes e eSIMs por meio de uma **Árvore B**, integrada à Tabela Hash da Etapa 1, preservando integralmente as funcionalidades já existentes.

### Requisitos da etapa

- Trabalhar com centenas de clientes; o enunciado recomenda aproximadamente **1.000 registros gerados automaticamente**, para observar buscas e inserções.
- Manter, em cada registro, ID único, nome, e-mail, eSIM, código do pacote e status. O **ID do cliente será a chave da Árvore B**.
- Carregar os registros persistidos na Árvore B durante a execução.
- Disponibilizar cadastro, consulta por ID, listagem e alteração de clientes na interface Web.
- Permitir a associação de eSIM e pacote ao cliente.
- Persistir os registros, podendo utilizar arquivos JSON.
- Realizar as buscas de clientes efetivamente na Árvore B, sem substituí-la por lista, dicionário ou biblioteca pronta.
- Manter a lógica da estrutura separada das rotas Flask; usar POST nas operações que alteram dados, preferencialmente com Post/Redirect/Get.
- Preservar cadastro, consulta, listagem, alteração, remoção, persistência e instrumentação dos países na Tabela Hash.
- Permitir consulta integrada **cliente × país de destino**: buscar o cliente pelo ID na Árvore B e consultar o código do destino na Tabela Hash, apresentando os dados do cliente, eSIM, pacote e informações de cobertura do país.
- Entregar a primeira implementação funcional do diferencial da equipe, quando aplicável. No diferencial já escolhido pelo projeto, isso corresponde à associação do pacote recomendado pelo roteiro ao cliente e seu eSIM na Árvore B.

### Exemplo de registro de cliente

```json
{
  "id": 58372,
  "nome": "Maria Silva",
  "email": "maria@email.com",
  "esim": "ESIM-83921",
  "pacote": 102,
  "status": "ativo"
}
```

### Pacotes de serviço
Os pacotes podem ser armazenados em JSON ou lista, pois não constituem outra estrutura principal. O enunciado apresenta o seguinte catálogo:

| Código | Pacote | Dados | Validade |
| --- | --- | --- | --- |
| 101 | Europa Basic | 5 GB | 15 dias |
| 102 | Europa Plus | 10 GB | 30 dias |
| 201 | América Basic | 5 GB | 15 dias |
| 202 | América Plus | 15 GB | 30 dias |
| 301 | Global | 20 GB | 30 dias |

### Implementação e uso
- `app/models/b_tree.py`: Árvore B existente, utilizada somente com ID inteiro como chave e posição do registro no arquivo como valor. A posição é o índice lógico (RRN, base zero) na lista JSON, e não um deslocamento em bytes. Os demais dados do cliente não ficam nos nós da árvore. Buscas e alterações encontram a posição na árvore e acessam o registro correspondente no arquivo; a listagem percorre o índice em ordem de ID. Novos registros são acrescentados ao final, e alterações preservam sua posição. Como a persistência usa uma lista JSON, o arquivo é desserializado para acessar uma posição; não se realiza busca por ID na lista.
- `app/models/client_service.py`: validação, carga, cadastro, consulta, alteração e integração com países. O ID é imutável e duplicatas são rejeitadas.
- `app/repository/client_repository.py`: leitura e gravação de `app/data/clients.json`. As gravações substituem o arquivo de forma atômica; o JSON serve para persistência, e a busca é realizada na árvore em memória.
- `app/data/packages.json`: catálogo auxiliar compartilhado com a recomendação de pacotes por roteiro.
- `app/routes/clients.py` e `app/templates/clients.html`: formulários Jinja, alterações via POST com redirecionamento e listagem em páginas de 50 clientes.
- Instrumentação existente da árvore: total de clientes, altura, número de nós, chaves da raiz e comparações na busca. Na consulta de destino, também são mostradas as comparações da Tabela Hash.

O projeto inclui **1.000 clientes fictícios**, com IDs de **10001 a 11000** e e-mails no domínio `example.com`. Eles são carregados na Árvore B ao iniciar a aplicação. Para acrescentar mais registros de demonstração, preservando os clientes existentes:

```bash
python -m flask --app run gerar-clientes --quantidade 1000
```

Acesse `/clientes/` pelo menu **Clientes & eSIMs**. Para demonstrar a integração, consulte o ID `10001` com destino `IT`. Para demonstrar o diferencial, analise `PT, ES, FR, IT` e associe a recomendação ao cliente. O cadastro e a edição permitem informar nome, e-mail, eSIM, pacote e status (`ativo`, `inativo` ou `suspenso`).

### Checklist de entrega
Funcionalidades implementadas e verificadas pelos testes automatizados da aplicação.

- [x] Etapa 1 preservada e integrada.
- [x] Implementação funcional da Árvore B.
- [x] Carga do conjunto de clientes.
- [x] Cadastro, busca por ID, listagem e alteração de clientes.
- [x] Associação de eSIM e pacote e persistência dos registros.
- [x] Integração cliente × país de destino.
- [x] Primeira implementação funcional do diferencial, quando aplicável.

Fonte: enunciado do trabalho prático 2026.2, seção da Etapa 2 (páginas 4 a 6), com as regras gerais de implementação e persistência aplicáveis à etapa.

---

## Diferencial da Equipe: Recomendação de Pacote de Dados a partir do Roteiro de Viagem

### Problema Resolvido
Viajantes internacionais frequentemente visitam múltiplos países em uma única viagem e precisam saber rapidamente se todos os destinos possuem cobertura eSIM e qual pacote de dados oferece a melhor relação de franquia e cobertura regional.

### Integração por Etapas
1. **Etapa 1 (Tabela Hash)**: O viajante informa a sequência de países do seu roteiro (ex.: `PT, ES, FR, IT`). O sistema realiza buscas sucessivas em tempo médio $O(1)$ na `HashTable`, contabiliza o total de comparações, separa destinos cobertos/não cobertos e analisa o conjunto de regiões atendidas para recomendar automaticamente entre os pacotes `Europa Basic (101)`, `Europa Plus (102)`, `América Basic (201)`, `América Plus (202)` ou `Global (301)`.
2. **Etapa 2 (Árvore B)**: Permite associar o pacote recomendado pelo roteiro ao cliente e seu `eSIM`. Na página de clientes, informe o ID e os destinos, analise o roteiro e confirme a associação. O servidor recalcula a recomendação ao receber o POST e impede a associação quando algum destino não tem cobertura.
3. **Etapa 3 (Grafos)**: Integrará o roteiro de múltiplos destinos ao Grafo ponderado da rede internacional para calcular a latência acumulada entre os países da viagem via algoritmo de Dijkstra.

---

## Como Executar o Projeto (Windows e Linux)

### 1. Criar e ativar o ambiente virtual (`venv`)

**No Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**No Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**No Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

### 2. Instalar as dependências
```bash
pip install -r requirements.txt
```

### 3. Executar a aplicação Flask
```bash
python run.py
```

Acesse no navegador:
- Página Inicial / Consulta de Cobertura / Roteiro: http://127.0.0.1:5000/
- Painel Administrativo / Instrumentação da Tabela Hash: http://127.0.0.1:5000/admin/
- Clientes / eSIMs / Árvore B / Consulta integrada: http://127.0.0.1:5000/clientes/

### 4. Executar os Testes Automatizados
```bash
python -m pytest -v
```

Os testes da Etapa 2 verificam o balanceamento da Árvore B com 1.000 registros, correspondência entre chaves e clientes após divisões, persistência e recarga, rejeição de IDs duplicados, alteração de chaves promovidas, integração com a Tabela Hash, associação de recomendação e rotas HTTP.
