#!/bin/bash

# Verificar se o arquivo .env existe e está preenchido
if [ ! -f .env ]; then
    echo "Arquivo .env não encontrado. Criando um modelo..."
    cat > .env << EOL
# Credenciais da AWS
AWS_ACCESS_KEY_ID=sua_access_key_aqui
AWS_SECRET_ACCESS_KEY=sua_secret_key_aqui
AWS_REGION=us-east-1

# Configuração do DynamoDB
DYNAMODB_TABLE_NAME=fezinhai_lotofacil_concursos
EOL
    echo "Por favor, edite o arquivo .env com suas credenciais antes de continuar."
    exit 1
fi

# Verificar se as credenciais AWS foram definidas no .env
if grep -q "AWS_ACCESS_KEY_ID=sua_access_key_aqui" .env; then
    echo "As credenciais AWS no arquivo .env não foram configuradas. Por favor, atualize-as antes de continuar."
    exit 1
fi

# Antes de executar este script, certifique-se de que o AWS CLI está configurado
# com as credenciais corretas para acessar o DynamoDB e gerenciar funções Lambda

# Create a deployment package
echo "Creating deployment package..."

# Create a deployment directory
mkdir -p deployment
rm -rf deployment/*

# Copy the necessary files
cp lambda_function.py entity.py requirements.txt .env deployment/

# Change to the deployment directory
cd deployment

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -t .

# Create the ZIP file
echo "Creating ZIP file..."
zip -r ../function.zip .

# Clean up
cd ..
echo "Deployment package created as function.zip"

echo "To deploy, run:"
echo "aws lambda update-function-code --function-name fezinhai-analisis-lambda --zip-file fileb://function.zip" 