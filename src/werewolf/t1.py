import os
import json
import time
import requests

USDA_API_KEY = 'Bc6H4leueBkJ0pjSPSIRJCGGXBecrC62iS8QMUqJ'

CACHE_FILE = f'{DATA_DIR}/usda_api_cache.json'

os.makedirs(DATA_DIR, exist_ok=True)

# --- Загрузка кэша ---
def load_cache(cache_file):
    try:
        with open(cache_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# --- Сохранение кэша ---
def save_cache(cache, cache_file):
    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=4)


# Обертка для запроса к API с обработкой ошибок
def get_nutrition_from_usda(ingredient, api_key, max_retries = 3, retry_delay = 2):
    base_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {
        'api_key': api_key,
        'query': ingredient,
        'pageSize': 1,
        'dataType': ["Foundation"]
    }
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data['foods']:
                # Берем нутриенты из первого найденного продукта
                return data['foods'][0].get('foodNutrients', [])
            else:
                return None
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе к API для '{ingredient}': {e}")
            if e.response.status_code == 429:
                time.sleep(retry_delay)
                retries += 1
            elif e.response.status_code == 500:
                time.sleep(retry_delay)
                retries += 1
            else:
                return None
        except Exception as e:
            print(f"Неизвестная ошибка при запросе для '{ingredient}': {e}")
            return None
    return None

def is_ingredient(ingredient, api_key):
    nutrients = get_nutrition_from_usda(ingredient, api_key)
    if nutrients:
        return True
    else:
        return False
    
def preprocess_ingredient(ingredient):
    ingredient = ingredient.replace('/', ' ')
    return ingredient
    
def filter_ingredients(df, api_key):
    # --- Инициализация кэша ---
    api_cache = load_cache(CACHE_FILE)

    not_ingredient = []
    yes_ingredient = []
    for column in df.columns.tolist():
        if column in api_cache:
            if api_cache[column]:
                yes_ingredient.append(column)
            else:
                not_ingredient.append(column)
        else:
            result = is_ingredient(preprocess_ingredient(column), api_key)
            api_cache[column] = result
            if result:
                yes_ingredient.append(column)
            else:
                not_ingredient.append(column)
            
    save_cache(api_cache, CACHE_FILE)

    return yes_ingredient, not_ingredient

yes_ingredient, not_ingredient = filter_ingredients(df, USDA_API_KEY)

# Определение признаков (X) и цели (y)
X = df[yes_ingredient]
print(f"\nОпределение признаков (X), размерность: {X.shape}")

y = df['rating']
print(f"Определение цели (y), размерность: {y.shape}")


# Разделение данных на обучающую и тестовую выборки (для регрессии)

# Константа для воспроизводимости
RANDOM_STATE = 42

from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.25,
    random_state=RANDOM_STATE
)

print(f"\nРазмеры выборок:")
print(f"  Обучающая (X_train, y_train): {X_train.shape}, {y_train.shape}")
print(f"  Тестовая (X_test, y_test):   {X_test.shape}, {y_test.shape}")
