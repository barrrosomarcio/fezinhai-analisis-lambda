import json
import os
import sys
from lambda_function import lambda_handler
from dotenv import load_dotenv

def check_env_config():
    """Verifica se o arquivo .env está corretamente configurado"""
    # Carregar variáveis de ambiente
    load_dotenv()
    
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

def main():
    """Execute lambda_handler e exibe os resultados formatados"""
    # Verificar se o ambiente está configurado
    if not check_env_config():
        sys.exit(1)
    
    print("🔍 Executando lambda_handler e consultando o DynamoDB...")
    
    try:
        # Chamar a função lambda_handler com um evento vazio
        response = lambda_handler({}, None)
        
        # Verificar o status
        if response['statusCode'] == 200:
            print("\n✅ Execução bem-sucedida!\n")
            
            # Analisar o corpo da resposta
            body = json.loads(response['body'])
            
            # Exibir o último resultado
            if body.get('last_result'):
                last = body['last_result']
                print("=== ÚLTIMO RESULTADO ===")
                print(f"Concurso: {last.get('concurso')}")
                print(f"Data: {last.get('data')}")
                print(f"Dezenas: {', '.join(last.get('dezenas', []))}")
                print(f"Acumulou: {'Sim' if last.get('acumulou') else 'Não'}")
                if 'acumuladaProxConcurso' in last:
                    print(f"Valor acumulado: R$ {last.get('acumuladaProxConcurso', 0):,.2f}")
                print()
            
            # Exibir estatísticas de frequência
            print("=== ESTATÍSTICAS DE FREQUÊNCIA ===")
            print(f"{'Número':<10}{'Quantidade':<10}")
            print("-" * 20)
            
            for item in body['frequency_stats'][:10]:  # Mostrar apenas os 10 primeiros
                print(f"{item['number']:<10}{item['quantity']:<10}")
            
            # Exibir estatísticas de tempo médio entre sorteios
            if 'average_gap_stats' in body:
                print("\n=== TEMPO MÉDIO ENTRE SORTEIOS ===")
                print(f"{'Número':<8}{'Média':<8}{'Mediana':<8}{'Mín':<6}{'Máx':<6}{'Aparições':<10}")
                print("-" * 46)
                
                for item in body['average_gap_stats'][:10]:  # Mostrar apenas os 10 primeiros
                    print(f"{item['number']:<8}{item['avg_gap']:<8.2f}{item['median_gap']:<8}{item['min_gap']:<6}{item['max_gap']:<6}{item['total_appearances']:<10}")
            
            print("\n=== TOP 15 NÚMEROS E SEUS COMPANHEIROS ===")
            for num_data in body['companion_stats']:
                number = num_data['number']
                print(f"\nNúmero {number} - Top 5 companheiros:")
                print(f"{'Número':<10}{'Quantidade':<10}")
                print("-" * 20)
                
                for comp in num_data['most_frequent'][:5]:  # Mostrar apenas os 5 primeiros companheiros
                    print(f"{comp['number']:<10}{comp['quantity']:<10}")
        else:
            print(f"❌ Erro ao executar: {response['body']}")
    except Exception as e:
        print(f"❌ Erro ao executar o Lambda: {str(e)}")
        print("\nVerifique se:")
        print("1. Suas credenciais AWS estão corretas")
        print("2. A tabela DynamoDB existe e está acessível")
        print("3. Você tem permissão para acessar o DynamoDB")

if __name__ == "__main__":
    main() 