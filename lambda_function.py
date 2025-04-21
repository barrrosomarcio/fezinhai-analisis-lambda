import boto3
import json
import os
from decimal import Decimal
from typing import List, Dict, Any, TypedDict
from entity import LotofacilResultEntity
from dotenv import load_dotenv
from statistics import mean, median
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
import requests

load_dotenv()

dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.getenv('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

table = dynamodb.Table(os.getenv('DYNAMODB_TABLE_NAME', 'fezinhai_lotofacil_concursos'))

class NumberCount(TypedDict):
    number: str
    quantity: int
    
class NumberWithCompanions(TypedDict):
    number: str
    most_frequent: List[NumberCount]

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def get_lotofacil_results() -> List[Dict[str, Any]]:
    try:
        items = []
        response = table.scan()
        items.extend(response.get('Items', []))
        
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
        
        unique_items = {item['concurso']: item for item in items}.values()
        
        return list(unique_items)
    except Exception as e:
        print(f"Erro ao acessar DynamoDB: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def count_number_frequencies(results: List[Dict[str, Any]]) -> List[NumberCount]:
    try:
        number_counts = {str(i).zfill(2): 0 for i in range(1, 26)}
        
        for result in results:
            if 'dezenas' in result:
                dezenas = result['dezenas']
                for number in dezenas:
                    if isinstance(number, int):
                        number = str(number).zfill(2)
                    elif isinstance(number, str) and len(number) == 1:
                        number = number.zfill(2)
                        
                    if number in number_counts:
                        number_counts[number] = number_counts.get(number, 0) + 1
        
        formatted_counts = [
            {"number": number, "quantity": count} 
            for number, count in number_counts.items()
        ]
        
        result = sorted(formatted_counts, key=lambda x: x["quantity"], reverse=True)
        return result
    except Exception as e:
        print(f"Erro ao contar frequências: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def find_most_frequent_companions(results: List[Dict[str, Any]], top_numbers: List[NumberCount]) -> List[NumberWithCompanions]:
    try:
        companions_result = []
        
        numbers_to_process = min(15, len(top_numbers))
        
        for number_data in top_numbers[:numbers_to_process]:
            number = number_data["number"]
            
            companion_counts = {str(i).zfill(2): 0 for i in range(1, 26) if str(i).zfill(2) != number}
            
            for result in results:
                if 'dezenas' not in result:
                    continue
                    
                dezenas = result['dezenas']
                normalized_dezenas = []
                for n in dezenas:
                    if isinstance(n, int):
                        normalized_dezenas.append(str(n).zfill(2))
                    elif isinstance(n, str):
                        normalized_dezenas.append(n.zfill(2) if len(n) == 1 else n)
                
                if number in normalized_dezenas:
                    for companion in normalized_dezenas:
                        if companion != number and companion in companion_counts:
                            companion_counts[companion] = companion_counts.get(companion, 0) + 1
            
            top_companions = sorted(
                [{"number": n, "quantity": c} for n, c in companion_counts.items() if c > 0],
                key=lambda x: x["quantity"],
                reverse=True
            )
            
            max_companions = min(14, len(top_companions))
            top_companions = top_companions[:max_companions]
            
            companions_result.append({
                "number": number,
                "most_frequent": top_companions
            })
        
        return companions_result
    except Exception as e:
        print(f"Erro ao encontrar companheiros: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def calculate_average_gap(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    try:
        sorted_results = sorted(results, key=lambda x: x.get('concurso', 0))
        
        last_appearance = {str(i).zfill(2): None for i in range(1, 26)}
        gaps = {str(i).zfill(2): [] for i in range(1, 26)}
        
        for result in sorted_results:
            if 'dezenas' not in result or 'concurso' not in result:
                print(f"Resultado sem dezenas ou concurso: {result.keys()}")
                continue
                
            concurso = result['concurso']
            dezenas = result['dezenas']
            
            for num in range(1, 26):
                num_str = str(num).zfill(2)
                
                if num_str in dezenas:
                    if last_appearance[num_str] is not None:
                        gap = concurso - last_appearance[num_str]
                        gaps[num_str].append(gap)
                    
                    last_appearance[num_str] = concurso
        
        avg_gaps = []
        for num in range(1, 26):
            num_str = str(num).zfill(2)
            
            if len(gaps[num_str]) > 0:
                avg_gap = mean(gaps[num_str])
                med_gap = median(gaps[num_str])
                min_gap = min(gaps[num_str])
                max_gap = max(gaps[num_str])
            else:
                avg_gap = 0
                med_gap = 0
                min_gap = 0
                max_gap = 0
                
            avg_gaps.append({
                "number": num_str,
                "avg_gap": round(avg_gap, 2),  # Arredondar para 2 casas decimais
                "median_gap": med_gap,
                "min_gap": min_gap,
                "max_gap": max_gap,
                "total_appearances": len(gaps[num_str]) + 1 if last_appearance[num_str] is not None else 0
            })
        
        result = sorted(avg_gaps, key=lambda x: x["avg_gap"])
        return result
    except Exception as e:
        print(f"Erro ao calcular average_gap: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def predict_next_combinations(frequency_stats: List[NumberCount], companion_stats: List[NumberWithCompanions], average_gap_stats: List[Dict[str, Any]]) -> List[List[str]]:
    import random
    
    possible_combinations = []
    
    top_numbers = [num['number'] for num in frequency_stats[:10]]
    top_gap_numbers = [num['number'] for num in sorted(average_gap_stats, key=lambda x: x['avg_gap'])[:5]]
    combined_top_numbers = list(set(top_numbers + top_gap_numbers))
    
    for _ in range(10):
        combination = set(combined_top_numbers)
        
        for number in combined_top_numbers:
            companions = next((comp['most_frequent'] for comp in companion_stats if comp['number'] == number), [])
            companions = [comp['number'] for comp in companions]
            
            while len(combination) < 15 and companions:
                companion = random.choice(companions)
                combination.add(companion)
                companions.remove(companion)
        
        while len(combination) < 15:
            random_number = str(random.randint(1, 25)).zfill(2)
            combination.add(random_number)
        
        possible_combinations.append(sorted(combination))
    
    return possible_combinations

def train_and_predict_combinations(results: List[Dict[str, Any]]) -> Dict[str, List[List[str]]]:
    X = []  # Características
    y = []  # Rótulos
    
    for result in results:
        if 'dezenas' in result:
            dezenas = result['dezenas']
            X.append([int(num) for num in dezenas])
            y.append(1)  # Rótulo fictício, pois estamos prevendo combinações
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    dt_model = DecisionTreeClassifier()
    dt_model.fit(X_train, y_train)
    
    knn_model = KNeighborsClassifier(n_neighbors=3)
    knn_model.fit(X_train, y_train)
    
    dt_predictions = dt_model.predict(X_test[:5])  # Prever 5 combinações
    knn_predictions = knn_model.predict(X_test[:5])  # Prever 5 combinações
    
    dt_combinations = [sorted([str(num).zfill(2) for num in X_test[i]]) for i in range(len(dt_predictions))]
    knn_combinations = [sorted([str(num).zfill(2) for num in X_test[i]]) for i in range(len(knn_predictions))]
    
    return {
        'DecisionTree': dt_combinations,
        'KNN': knn_combinations
    }


def login_api() -> str:

    api_url = os.environ.get('API_URL')
    if not api_url:
        raise Exception("API_URL environment variable not set")

    email = os.environ.get('API_EMAIL')
    password = os.environ.get('API_PASSWORD')
    
    if not email or not password:
        raise Exception("API_EMAIL and API_PASSWORD environment variables must be set")

    login_url = f"{api_url}/auth/login"  # Ajuste o endpoint conforme necessário
    
    login_data = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data.get('accessToken')
        
        if not access_token:
            raise Exception("No access token in response")
            
        return access_token
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to login: {str(e)}")

def send_data_to_api(data: Dict[str, Any], api_url: str) -> None:
    try:
        # Converter a string JSON para um dicionário
        data_dict = json.loads(data)
        access_token = login_api()
        headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

        response = requests.post(f"{api_url}/lotofacil/analisys", json=data_dict, headers=headers)
        response.raise_for_status()
        print(f"Dados enviados com sucesso para a API: {response.status_code}")

        # for key, value in data_dict.items():
        #     payload = {key: value}
        #     print(f"Enviando {key} para a API...")
        #     response = requests.post(api_url, json=payload)
        #     response.raise_for_status()
        #     print(f"Dados de {key} enviados com sucesso para a API: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar dados para a API: {e}")

def lambda_handler(event, context):
    try:
        print("Iniciando lambda_handler...")
        results = get_lotofacil_results()
        print(f"Resultados obtidos: {len(results)} itens")
        
        if not results:
            raise Exception("Nenhum resultado encontrado na tabela DynamoDB")
            
        frequency_stats = count_number_frequencies(results)
        
        companion_stats = find_most_frequent_companions(results, frequency_stats)

        average_gap_stats = calculate_average_gap(results)

        simple_predictions = predict_next_combinations(frequency_stats, companion_stats, average_gap_stats)

        trained_predictions = train_and_predict_combinations(results)

        last_result = None
        if results:
            sorted_results = sorted(results, key=lambda x: x.get('concurso', 0), reverse=True)
            last_result = sorted_results[0] if sorted_results else None
                
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'frequency_stats': frequency_stats,
                'companion_stats': companion_stats,
                'last_result': last_result,
                'average_gap_stats': average_gap_stats,
                'simple_predictions': simple_predictions,
                'trained_predictions': trained_predictions
            }, cls=DecimalEncoder)
        }

        api_url = os.getenv('API_URL')
        if api_url:
            send_data_to_api(response['body'], api_url)
        else:
            print("API_URL não está definida nas variáveis de ambiente.")

        return response
    
    except Exception as e:
        print(f"ERRO: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        } 