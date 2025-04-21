# fezinhai-analisis-lambda

AWS Lambda function para análise de resultados da Lotofácil armazenados no DynamoDB, incluindo previsões usando Inteligência Artificial.

## Funcionalidades

1. Consulta os resultados da Lotofácil na tabela `fezinhai_lotofacil_concursos` do DynamoDB
2. Gera estatísticas de frequência para os números de 1 a 25
3. Analisa os padrões de acompanhamento para os 15 números mais frequentes
4. Retorna o resultado mais recente da Lotofácil
5. Calcula o tempo médio entre sorteios para cada número
6. **NOVO**: Gera previsões de combinações usando análise de dados e Inteligência Artificial
7. **NOVO**: Envia os resultados das análises para uma API externa

## Formato de Saída

A função Lambda retorna:

1. `frequency_stats`: Array de objetos com `number` e `quantity` mostrando a frequência de cada número
2. `companion_stats`: Para cada um dos 15 números mais frequentes, mostra os 14 números que mais frequentemente os acompanham
3. `last_result`: O resultado mais recente da Lotofácil (concurso com maior número)
4. `average_gap_stats`: Tempo médio entre sorteios para cada número, incluindo média, mediana, mínimo e máximo
5. **NOVO**: `simple_predictions`: 10 combinações de 15 números geradas usando estatísticas de frequência e intervalo
6. **NOVO**: `trained_predictions`: Combinações geradas por dois modelos de aprendizado de máquina diferentes (Decision Tree e KNN)

## Análises Disponíveis

- **Análise de Frequência**: Ordena os números de 01 a 25 por frequência de ocorrência
- **Análise de Companheiros**: Para cada número frequente, identifica quais outros números tendem a acompanhá-lo
- **Análise de Intervalos**: Calcula quanto tempo (em concursos) cada número costuma ficar sem ser sorteado
- **NOVO**: **Previsão Heurística**: Gera combinações com base em estatísticas de frequência e intervalos
- **NOVO**: **Previsão por IA**: Usa modelos de aprendizado de máquina para prever possíveis combinações futuras

## Integração com API

**NOVO**: Os resultados das análises são automaticamente enviados para uma API externa para armazenamento e visualização. A integração suporta autenticação com token JWT.

## Configuração

1. Crie um ambiente virtual:
   ```
   python -m virtualenv venv
   source venv/bin/activate  # Linux/MacOS
   venv\Scripts\activate     # Windows
   ```

2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

3. Configure o arquivo `.env` com suas credenciais:
   ```
   # Credenciais da AWS
   AWS_ACCESS_KEY_ID=sua_access_key_aqui
   AWS_SECRET_ACCESS_KEY=sua_secret_key_aqui
   AWS_REGION=us-east-1
   
   # Configuração do DynamoDB
   DYNAMODB_TABLE_NAME=fezinhai_lotofacil_concursos
   
   # NOVO: Configuração da API
   API_URL=https://sua-api.com
   API_EMAIL=seu_email@exemplo.com
   API_PASSWORD=sua_senha
   ```

## Execução Local

Para executar o projeto localmente:
```
python test_local.py
```

## Implantação

1. Verifique se a tabela DynamoDB `fezinhai_lotofacil_concursos` existe e contém os dados necessários
2. Execute o script de deploy: `./deploy.sh`
3. A função estará disponível como `fezinhai-analisis-lambda`

## Testes

Para executar os testes, execute:
```
python test_lambda.py
```

Este comando testará a função localmente fazendo uma consulta real ao DynamoDB.