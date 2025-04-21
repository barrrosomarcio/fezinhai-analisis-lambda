import boto3
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def check_table():
    """Verificação rápida da tabela DynamoDB"""
    print("\n=== VERIFICAÇÃO RÁPIDA DA TABELA DYNAMODB ===")
    
    # Obter configurações
    table_name = os.getenv('DYNAMODB_TABLE_NAME', 'fezinhai_lotofacil_concursos')
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    try:
        # Conectar ao DynamoDB
        print(f"Conectando ao DynamoDB na região {region}...")
        resource = boto3.resource('dynamodb',
                              region_name=region,
                              aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                              aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
        
        # Tentar acessar a tabela
        print(f"Acessando a tabela '{table_name}'...")
        table = resource.Table(table_name)
        
        # Fazer uma consulta simples
        print("Fazendo uma consulta simples...")
        response = table.scan(Limit=1)
        
        # Verificar se há itens
        if 'Items' in response and len(response['Items']) > 0:
            item = response['Items'][0]
            print("\n✅ SUCESSO: Tabela acessada com sucesso!")
            print(f"Total de itens encontrados: {response.get('Count', 0)}")
            
            # Verificar campos chave
            if 'dezenas' in item:
                print(f"Campo 'dezenas' encontrado: {item['dezenas']}")
            else:
                print("⚠️ AVISO: Campo 'dezenas' não encontrado no item.")
                print(f"Campos disponíveis: {list(item.keys())}")
                
            if 'concurso' in item:
                print(f"Campo 'concurso' encontrado: {item['concurso']}")
                
            return True
        else:
            print("\n⚠️ AVISO: A tabela existe mas não tem itens.")
            return False
            
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        
        # Oferecer sugestões com base no erro
        error_str = str(e).lower()
        if "not found" in error_str or "resource:notfound" in error_str:
            print("\nSUGESTÃO: A tabela parece não existir. Certifique-se que:")
            print("1. O nome da tabela está correto no arquivo .env")
            print("2. A tabela foi criada na região especificada")
            print("3. Você tem acesso à tabela com as credenciais fornecidas")
        elif "access denied" in error_str or "not authorized" in error_str:
            print("\nSUGESTÃO: Problema de permissões. Certifique-se que:")
            print("1. Suas credenciais AWS estão corretas")
            print("2. O usuário tem permissão para acessar DynamoDB")
            print("3. O usuário tem acesso à tabela específica")
        
        return False

if __name__ == "__main__":
    check_table() 