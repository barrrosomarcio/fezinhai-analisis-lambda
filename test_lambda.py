import json
import boto3
import os
import sys
from lambda_function import lambda_handler, count_number_frequencies, find_most_frequent_companions
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def check_env_config():
    """Verifica se o arquivo .env está corretamente configurado"""
    # Verificar as variáveis essenciais
    required_vars = [
        'AWS_ACCESS_KEY_ID', 
        'AWS_SECRET_ACCESS_KEY', 
        'AWS_REGION', 
        'DYNAMODB_TABLE_NAME'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var) == f'sua_{var.lower()}_aqui':
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Arquivo .env não está configurado corretamente.")
        print(f"As seguintes variáveis precisam ser configuradas: {', '.join(missing_vars)}")
        print("\nEdite o arquivo .env com suas credenciais AWS e tente novamente.")
        return False
    
    return True

def test_count_frequencies():
    """Test the frequency counting function"""
    sample_results = [
        {'dezenas': ['01', '03', '05', '07', '09']},
        {'dezenas': ['01', '03', '06', '08', '09']},
        {'dezenas': ['02', '04', '06', '08', '10']}
    ]
    
    frequencies = count_number_frequencies(sample_results)
    
    # Verify most frequent numbers
    assert frequencies[0]['number'] == '03' or frequencies[0]['number'] == '01' or frequencies[0]['number'] == '09'
    assert frequencies[0]['quantity'] == 2
    
    print("✅ Frequency test passed!")
    return frequencies

def test_companion_analysis(frequencies):
    """Test the companion analysis function"""
    sample_results = [
        {'dezenas': ['01', '03', '05', '07', '09']},
        {'dezenas': ['01', '03', '06', '08', '09']},
        {'dezenas': ['02', '04', '06', '08', '10']}
    ]
    
    companions = find_most_frequent_companions(sample_results, frequencies[:5])
    
    # Verify companions for number '01'
    number_01_data = next((item for item in companions if item['number'] == '01'), None)
    if number_01_data:
        # '03' and '09' should be common companions to '01'
        companion_numbers = [comp['number'] for comp in number_01_data['most_frequent']]
        assert '03' in companion_numbers
        assert '09' in companion_numbers
    
    print("✅ Companions test passed!")

def test_lambda_handler():
    """Test the complete lambda handler with real DynamoDB connection"""
    # Call the lambda handler with a dummy event
    result = lambda_handler({}, {})
    
    # Exibir detalhes do resultado
    print(f"\nCódigo de status: {result.get('statusCode')}")
    
    # Verificar se o resultado está correto
    if result.get('statusCode') == 200:
        # Verificar a resposta
        try:
            response_body = json.loads(result['body'])
            
            # Verificar as partes da resposta
            print(f"Chaves na resposta: {list(response_body.keys())}")
            
            # Verificar frequency_stats
            frequency_stats = response_body.get('frequency_stats', [])
            print(f"frequency_stats: {len(frequency_stats)} itens")
            
            # Verificar companion_stats
            companion_stats = response_body.get('companion_stats', [])
            print(f"companion_stats: {len(companion_stats)} itens")
            
            # Verificar last_result
            last_result = response_body.get('last_result')
            if last_result:
                print(f"last_result: concurso {last_result.get('concurso')}")
            else:
                print("last_result: Não encontrado")
                
            # Verificar average_gap_stats
            average_gap_stats = response_body.get('average_gap_stats', [])
            print(f"average_gap_stats: {len(average_gap_stats)} itens")
            
            # Imprimir os resultados
            print("\n✅ Lambda handler test passou!")
            
            # Print the top 5 most frequent numbers
            print("\nTop 5 most frequent numbers:")
            for i, num in enumerate(frequency_stats[:5]):
                print(f"{i+1}. Number {num['number']}: {num['quantity']} occurrences")
            
            # Print the top 5 numbers with lowest average gap
            print("\nTop 5 numbers with lowest average gap between draws:")
            for i, num in enumerate(average_gap_stats[:5]):
                print(f"{i+1}. Number {num['number']}: {num['avg_gap']} concursos (média), {num['median_gap']} (mediana)")
            
            # Print companion stats for the most frequent number
            if companion_stats:
                most_frequent = companion_stats[0]['number']
                print(f"\nCompanion numbers for {most_frequent} (the most frequent number):")
                for i, comp in enumerate(companion_stats[0]['most_frequent'][:5]):
                    print(f"{i+1}. Number {comp['number']}: {comp['quantity']} occurrences")
                    
            return True
                
        except Exception as e:
            print(f"❌ Erro ao analisar a resposta: {str(e)}")
            print(f"Resposta bruta: {result.get('body')}")
            import traceback
            traceback.print_exc()
            return False
    else:
        # Houve um erro
        print(f"❌ Lambda retornou erro (status {result.get('statusCode')})")
        try:
            error_body = json.loads(result.get('body', '{}'))
            print(f"Erro: {error_body.get('error', 'Desconhecido')}")
        except:
            print(f"Corpo da resposta: {result.get('body')}")
        return False

if __name__ == "__main__":
    # Verificar se o ambiente está configurado
    if not check_env_config():
        sys.exit(1)
        
    # Run the unit tests with static data
    print("🔬 Running unit tests with static data...")
    frequencies = test_count_frequencies()
    
    print("\n🔬 Running companions test...")
    test_companion_analysis(frequencies)
    
    # Run the test with real DynamoDB connection
    print("\n🔍 Running lambda handler test with real DynamoDB connection...")
    try:
        # Testar conexão com o DynamoDB
        print("Verificando conexão com o DynamoDB...")
        from boto3 import client
        ddb_client = client('dynamodb', 
                          region_name=os.getenv('AWS_REGION'),
                          aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                          aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
        
        try:
            # Listar tabelas para verificar se conseguimos conectar
            tables = ddb_client.list_tables()
            print(f"Tabelas disponíveis: {', '.join(tables['TableNames'])}")
            
            # Verificar se a tabela existe
            table_name = os.getenv('DYNAMODB_TABLE_NAME')
            if table_name in tables['TableNames']:
                print(f"✅ Tabela '{table_name}' encontrada!")
                
                # Verificar se existem itens na tabela
                table = boto3.resource('dynamodb').Table(table_name)
                try:
                    scan_result = table.scan(Limit=1)
                    if 'Items' in scan_result and len(scan_result['Items']) > 0:
                        print(f"✅ Tabela contém {scan_result.get('Count', 1)} item(s)")
                        
                        # Verificar campos essenciais no item
                        item = scan_result['Items'][0]
                        if 'dezenas' in item:
                            print(f"✅ Campo 'dezenas' encontrado: {item['dezenas']}")
                        else:
                            print("❌ Campo 'dezenas' NÃO encontrado no item")
                            print(f"Campos disponíveis: {list(item.keys())}")
                    else:
                        print("❌ Tabela está vazia")
                except Exception as scan_error:
                    print(f"❌ Erro ao fazer scan na tabela: {str(scan_error)}")
            else:
                print(f"❌ Tabela '{table_name}' não encontrada nas tabelas disponíveis!")
                
        except Exception as table_error:
            print(f"❌ Erro ao listar tabelas: {str(table_error)}")
        
        # Tentar executar o lambda handler
        lambda_success = test_lambda_handler()
        
        # Exibir mensagem final
        if lambda_success:
            print("\n✅ All tests completed successfully!")
        else:
            print("\n⚠️ Alguns testes passaram, mas o lambda_handler falhou.")
            print("   Verifique os logs acima para entender o erro.")
            print("   Você pode tentar executar 'python quick_check.py' para um diagnóstico mais detalhado.")
            
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        print("\nDetalhes do erro:")
        traceback.print_exc()
        print("\nVerifique se:")
        print("1. Suas credenciais AWS estão corretas")
        print("2. A tabela DynamoDB existe e está acessível")
        print("3. Você tem permissão para acessar o DynamoDB") 