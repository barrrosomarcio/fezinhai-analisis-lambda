import boto3
import os
import sys
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Cores para saída
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    
def print_color(text, color):
    print(f"{color}{text}{Colors.RESET}")

def check_env():
    """Verificar variáveis de ambiente"""
    print_color("1. Verificando variáveis de ambiente...", Colors.BLUE)
    
    required_vars = [
        'AWS_ACCESS_KEY_ID', 
        'AWS_SECRET_ACCESS_KEY', 
        'AWS_REGION', 
        'DYNAMODB_TABLE_NAME'
    ]
    
    all_ok = True
    for var in required_vars:
        value = os.getenv(var)
        if not value or value == f'sua_{var.lower()}_aqui':
            print_color(f"   ❌ {var} não configurado ou com valor padrão", Colors.RED)
            all_ok = False
        else:
            if var.startswith('AWS_SECRET'):
                value = value[:4] + '...' + value[-4:] if len(value) > 8 else '****'
            elif var.startswith('AWS_ACCESS'):
                value = value[:4] + '...' + value[-4:] if len(value) > 8 else '****'
            print_color(f"   ✅ {var} = {value}", Colors.GREEN)
            
    return all_ok

def test_aws_credentials():
    """Testar credenciais AWS"""
    print_color("\n2. Testando credenciais AWS...", Colors.BLUE)
    
    try:
        # Testar se conseguimos listar as tabelas do DynamoDB (em vez de regiões EC2)
        client = boto3.client('dynamodb', 
                             region_name=os.getenv('AWS_REGION'),
                             aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                             aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
        
        tables = client.list_tables()
        print_color(f"   ✅ Credenciais AWS válidas! ({len(tables['TableNames'])} tabelas disponíveis)", Colors.GREEN)
        
        # Mostrar as tabelas disponíveis
        if tables['TableNames']:
            print_color(f"   📋 Tabelas disponíveis: {', '.join(tables['TableNames'])}", Colors.YELLOW)
        else:
            print_color(f"   ℹ️ Não há tabelas disponíveis nesta conta/região", Colors.YELLOW)
            
        return True
    except Exception as e:
        print_color(f"   ❌ Erro ao validar credenciais: {str(e)}", Colors.RED)
        return False

def test_dynamodb_connection():
    """Testar conexão com a tabela DynamoDB específica"""
    print_color("\n3. Testando conexão com a tabela específica...", Colors.BLUE)
    
    try:
        table_name = os.getenv('DYNAMODB_TABLE_NAME')
        
        # Obter a lista de tabelas novamente
        ddb_client = boto3.client('dynamodb', 
                               region_name=os.getenv('AWS_REGION'),
                               aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                               aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
        
        tables = ddb_client.list_tables()
        
        # Verificar se a tabela específica existe
        if table_name in tables['TableNames']:
            print_color(f"   ✅ Tabela '{table_name}' encontrada!", Colors.GREEN)
            
            # Verificar se conseguimos fazer scan na tabela
            resource = boto3.resource('dynamodb', 
                                  region_name=os.getenv('AWS_REGION'),
                                  aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                                  aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
            
            table = resource.Table(table_name)
            
            try:
                response = table.scan(Limit=1)  # Tenta ler apenas 1 item para ser rápido
                
                if 'Items' in response and len(response['Items']) > 0:
                    print_color(f"   ✅ Leitura da tabela bem-sucedida! ({response.get('Count', 0)} itens lidos)", Colors.GREEN)
                    print_color(f"   🔍 Exemplo de estrutura de item: {list(response['Items'][0].keys())}", Colors.YELLOW)
                    # Verificar se tem o campo 'dezenas'
                    if 'dezenas' in response['Items'][0]:
                        print_color(f"   ✅ Campo 'dezenas' encontrado no item!", Colors.GREEN)
                        print_color(f"   🎯 Exemplo de dezenas: {response['Items'][0]['dezenas']}", Colors.YELLOW)
                    else:
                        print_color(f"   ❌ Campo 'dezenas' NÃO encontrado no item! Isso pode causar erros.", Colors.RED)
                        print_color(f"   ℹ️ Campos disponíveis: {list(response['Items'][0].keys())}", Colors.YELLOW)
                else:
                    print_color(f"   ⚠️ Tabela está vazia ou não foi possível ler itens.", Colors.YELLOW)
            except Exception as scan_error:
                print_color(f"   ❌ Erro ao ler tabela: {str(scan_error)}", Colors.RED)
                return False
        else:
            print_color(f"   ❌ Tabela '{table_name}' NÃO encontrada! Verifique se o nome está correto.", Colors.RED)
            print_color(f"   ℹ️ Tabelas disponíveis: {', '.join(tables['TableNames'])}", Colors.YELLOW)
            return False
            
        return True
    except Exception as e:
        print_color(f"   ❌ Erro ao testar conexão com DynamoDB: {str(e)}", Colors.RED)
        import traceback
        traceback.print_exc()
        return False

def test_permissions():
    """Testar permissões específicas do DynamoDB"""
    print_color("\n4. Testando permissões específicas...", Colors.BLUE)
    
    table_name = os.getenv('DYNAMODB_TABLE_NAME')
    
    operations = [
        {"name": "DescribeTable", "callable": lambda: boto3.client('dynamodb', region_name=os.getenv('AWS_REGION')).describe_table(TableName=table_name)},
        {"name": "Scan", "callable": lambda: boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION')).Table(table_name).scan(Limit=1)}
    ]
    
    all_ok = True
    for op in operations:
        try:
            op["callable"]()
            print_color(f"   ✅ {op['name']}: Permitido", Colors.GREEN)
        except Exception as e:
            print_color(f"   ❌ {op['name']}: Negado - {str(e)}", Colors.RED)
            all_ok = False
    
    return all_ok

def main():
    """Função principal para testar a conexão"""
    print_color("\n=== DIAGNÓSTICO DE CONEXÃO COM DYNAMODB ===", Colors.BLUE)
    
    # Verificar variáveis de ambiente
    if not check_env():
        print_color("\n❌ Configuração de ambiente incompleta. Corrija o arquivo .env e tente novamente.", Colors.RED)
        return
    
    # Testar credenciais AWS com DynamoDB
    if not test_aws_credentials():
        print_color("\n❌ Problemas com acesso ao DynamoDB. Verifique suas credenciais e permissões.", Colors.RED)
        print_color("   🔍 Certifique-se que o usuário tenha a política AmazonDynamoDBReadOnlyAccess ou similar.", Colors.YELLOW)
        return
    
    # Testar conexão com a tabela específica
    if not test_dynamodb_connection():
        print_color("\n❌ Problemas com a tabela especificada. Verifique o nome da tabela e permissões.", Colors.RED)
        return
    
    # Testar permissões específicas
    test_permissions()
    
    print_color("\n✅ Diagnóstico concluído com sucesso! Sua conexão com a tabela está funcionando.", Colors.GREEN)
    print_color("   Você pode executar o script principal agora: python test_local.py", Colors.GREEN)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_color("\nDiagnóstico interrompido pelo usuário.", Colors.YELLOW)
    except Exception as e:
        print_color(f"\nErro inesperado: {str(e)}", Colors.RED)
        import traceback
        traceback.print_exc() 