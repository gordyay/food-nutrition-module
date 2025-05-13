import pandas as pd
import joblib
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import json
import requests
from pathlib import Path
DATA_PATH='data/'

MODEL_PATH = f"{DATA_PATH}best_classifier_model.joblib"
NUTRITION_DATA_PATH = f"{DATA_PATH}data/nutrition_facts_dv.csv"
RECIPE_DATA_PATH = f"{DATA_PATH}recipes_for_similarity.csv"
api_key='ehlVSIKSMiugJZHlii3sU7OKCexe4MIlnYenGric'
nutrients_list = [
    "Total lipid (fat)",
    "Fatty acids, total saturated",
    "Fatty acids, total monounsaturated",
    "Fatty acids, total polyunsaturated",
    "Fatty acids, total trans",
    "Cholesterol",
    "Carbohydrate, by difference",
    "Sodium, Na", 
    "Fiber, total dietary",
    "Protein",
    "Sugars, Total",  
    "Energy", 
    "Vitamin A, RAE",  
    "Vitamin C, total ascorbic acid", 
    "Vitamin D (D2 + D3)",
    "Vitamin E (alpha-tocopherol)",
    "Vitamin K (phylloquinone)",
    "Thiamin",
    "Riboflavin",
    "Niacin",
    "Vitamin B-6",
    "Folate, total",
    "Vitamin B-12",
    "Calcium, Ca",
    "Iron, Fe",
    "Phosphorus, P",
    "Magnesium, Mg",
    "Zinc, Zn",
    "Copper, Cu",
    "Manganese, Mn",
    "Selenium, Se",
    "Potassium, K",
    "Ash",
    "Nitrogen",
    "Water",
    "Fructose",
    "Glucose",
    "Sucrose",
    "Galactose"
]

class NutritionApp:
    def __init__(self):
        """Loads necessary data and the trained model."""
        try:
            self.model = joblib.load(MODEL_PATH)
            if hasattr(self.model, 'feature_names_in_'):
                 self.ingredient_features = self.model.feature_names_in_
                 self.synonyms = self._build_synonyms()
            else:
                 # Handle error or load from separate file - essential step!
                 raise ValueError("Could not determine ingredient features from model.")
            self.daily_values = self._load_daily_values()
            if Path(RECIPE_DATA_PATH).exists():
                self.recipes_df = pd.read_csv(RECIPE_DATA_PATH)
            else:
                self.recipes_df = pd.read_csv(f"{RECIPE_DATA_PATH}.gz", compression='gzip')
            self.recipe_vectors = self.recipes_df[self.ingredient_features].values
        except FileNotFoundError as e:
            print(f"Error loading data file: {e}. Make sure research notebook generated files.")
            raise
        except Exception as e:
            print(f"Error initializing NutritionApp: {e}")
            raise
    def _load_daily_values(self):
        """Loads daily values from daily. tsv and returns the dictionary."""
        daily = pd.read_csv("data/daily.tsv", sep="\t")
        # Преобразуем в словарь {нут риент: значение}
        return dict(zip(daily['Nutrient'], daily['Daily Value'])) 
    


    def _build_synonyms(self):
        """Creates a dictionary of synonyms for ingredients with a slash or or."""
        synonyms = {}
        for ingredient in self.ingredient_features:
            if '/' in ingredient:
                parts = ingredient.split('/')
                for part in parts:
                    part = part.strip().lower()
                    synonyms[part] = ingredient  
            if ' or ' in ingredient:
                parts = ingredient.split(' or ')
                for part in parts:
                    part = part.strip().lower()
                    synonyms[part] = ingredient  
            synonyms[ingredient.lower()] = ingredient
        return synonyms
    


    def _convert_units(self, value, unit, nutrient):
        """Конвертирует единицы измерения в соответствии с daily.tsv."""
        # Предполагаем, что daily.tsv использует граммы (G) для большинства нутриентов,
        # но для некоторых — мг (MG) или мкг (UG).
        if unit == 'G':
            return value  # Граммы остаются без изменений
        elif unit == 'MG':
            if nutrient in self.daily_values and self.daily_values[nutrient] > 100:  # Предполагаем, что значение в граммах
                return value / 1000  # мг -> г
            return value  # Оставляем мг
        elif unit == 'UG':
            if nutrient in self.daily_values and self.daily_values[nutrient] > 100:  # Предполагаем, что значение в граммах
                return value / 1000000  # мкг -> г
            elif nutrient in self.daily_values and self.daily_values[nutrient] > 10:  # Предполагаем, что значение в мг
                return value / 1000  # мкг -> мг
            return value  # Оставляем мкг
        else:
            return value
        


    def is_ingredient_in_list(self, input_ingredient):
        """Checks the entered ingredient is in the list."""
        norm_input = input_ingredient.lower().strip()
        if norm_input in self.synonyms:
            return self.synonyms[norm_input]  
        return None  
        
               
    def _preprocess_input(self, ingredients_list):
        """Converts a list of ingredient names into a feature vector."""
        # Create a zero vector with the same columns as the training data
        input_vector = pd.DataFrame(np.zeros((1, len(self.ingredient_features))),
                                   columns=self.ingredient_features)
        # Mark ingredients present in the input list as 1
        count = 0
        for ingredient in ingredients_list:
            matched_ingredient = self.is_ingredient_in_list(ingredient)
            if matched_ingredient and matched_ingredient in input_vector.columns:
                input_vector[matched_ingredient] = 1
                count += 1
            else:
                print(f"Warning: Ingredient '{ingredient}' not in known features, ignoring.")
        if count == 0:
            print("Warning: None of the input ingredients were recognized.")
            return None
        return input_vector # Return the DataFrame/numpy array expected by model
    

    def predict_rating_class(self, ingredients_list):
        """Predicts the rating class ('bad', 'so-so', 'great') for a list of ingredients."""
        input_vector = self._preprocess_input(ingredients_list)
        if input_vector is None:
            return "unknown"
        try:
            prediction = self.model.predict(input_vector)
            return prediction[0]
        except Exception as e:
            print(f"Error during prediction: {e}")
            return "error"

    def get_nutrition_info(self, ingredients_list):
        def load_nutrients_cache(path_to_file):
            try:
                with open(path_to_file, 'r', encoding='utf-8') as f:
                    try:
                        return json.load(f)
                    except:
                        return {}
            except:
                return {}
        def save_to_cache(path_to_file, ingredient, nutrient_dict, cache):
            cache[ingredient]=nutrient_dict
            with open(path_to_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=4, ensure_ascii=False)

        def get_nutrients_raw_data(ingredient):
            # function that receives raw data on the nutrients of an ingredient
            ingredient_info=None
            params = {
                "query": f'"{ingredient}"',
                "api_key": api_key,
                "dataType": ["Foundation"]  
            }
            cache=load_nutrients_cache(f"{DATA_PATH}ingridient_nutr_cache.json")
            if not ingredient in cache:
                return cache[ingredient]
            else:
                response = requests.get('https://api.nal.usda.gov/fdc/v1/foods/search', params=params)
                if response.status_code == 200:
                    ingredient_info = response.json().get('foods')
                    if ingredient_info and ingredient_info[0].get('score') < 200:
                        ingredient_info=None
                    if ingredient_info:
                        ingredient_info=ingredient_info[0].get('foodNutrients')
                        nutrient_df=pd.json_normalize(ingredient_info)[['nutrientName','unitName','value']]
                        nutrient_dict=nutrient_df[nutrient_df['nutrientName'].isin(nutrients_list)].to_dict()       
                        save_to_cache(f"{DATA_PATH}ingridient_nutr_cache.json",ingredient, nutrient_dict, cache)
                        ingredient_info=nutrient_dict
            return ingredient_info
      
        """Retrieves nutrition information (%DV) for a list of ingredients."""
        results = {}
        for ingredient in ingredients_list:
            norm_ingredient = ingredient.lower().strip()
            nutrient_data= get_nutrients_raw_data(norm_ingredient)
            if nutrient_data:
                nutrient_dict = {}
                for idx in nutrient_data['nutrientName']:
                    nutrient_name = nutrient_data['nutrientName'][idx]
                    value = float(nutrient_data['value'][idx])
                    unit = nutrient_data['unitName'][idx]
                    converted_value = self._convert_units(value, unit, nutrient_name)
                    if nutrient_name in self.daily_values:
                        daily_value = self.daily_values[nutrient_name]
                        percent_dv = (converted_value / daily_value) * 100
                        nutrient_dict[nutrient_name] = round(percent_dv, 2)
                    results[norm_ingredient] = nutrient_dict
            else:
                results[ingredient] = {"error": "Nutritional data not found"}
        return results
    def find_similar_recipes(self, ingredients_list, n=3):
        """Finds the top N most similar recipes based on ingredients."""
        input_vector = self._preprocess_input(ingredients_list)
        if input_vector is None:
            return []

        input_vec_np = input_vector.values # Get numpy array

        try:
            # Calculate cosine similarities
            similarities = cosine_similarity(input_vec_np, self.recipe_vectors)

            # Get indices of top N similar recipes (excluding potential exact match)
            # argsort sorts in ascending order, [-n-1:-1] takes the top n excluding the last one (itself)
            # If the input isn't an existing recipe, the last one is just the most similar.
            # Let's take the top N directly. Add [0] because similarities is shape (1, num_recipes)
            sorted_indices = np.argsort(similarities[0])[::-1] # Descending order

            top_n_indices = sorted_indices[:n]

            # Get details for the top N recipes
            similar_recipes = []
            for i in top_n_indices:
                recipe_details = self.recipes_df.iloc[i]
                similar_recipes.append({
                    'title': recipe_details.get('title', 'N/A'), # Use .get for safety
                    'rating': recipe_details.get('rating', 'N/A'),
                    'url': recipe_details.get('url', 'N/A')
                })
            return similar_recipes
        except Exception as e:
            print(f"Error finding similar recipes: {e}")
            return []