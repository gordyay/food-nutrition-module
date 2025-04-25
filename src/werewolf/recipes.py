import pandas as pd
import joblib
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import random # For bonus

# Define constants for file paths (makes it easier to manage)
MODEL_PATH = 'data/best_classifier_model.joblib'
# Assuming you save the feature list, e.g. as a pickle file or list within the model object
# FEATURE_LIST_PATH = 'data/ingredient_features.pkl'
NUTRITION_DATA_PATH = 'data/nutrition_facts_dv.csv'
RECIPE_DATA_PATH = 'data/recipe_urls.csv'

class NutritionApp:
    def __init__(self):
        """Loads necessary data and the trained model."""
        try:
            self.model = joblib.load(MODEL_PATH)
            # If features aren't stored with model, load them separately
            # self.ingredient_features = joblib.load(FEATURE_LIST_PATH)
            # Often, sklearn pipelines store feature names, check model object
            if hasattr(self.model, 'feature_names_in_'):
                 self.ingredient_features = self.model.feature_names_in_
            else:
                 # Handle error or load from separate file - essential step!
                 raise ValueError("Could not determine ingredient features from model.")

            self.nutrition_df = pd.read_csv(NUTRITION_DATA_PATH).set_index('ingredient_name') # Assuming index col name
            self.recipes_df = pd.read_csv(RECIPE_DATA_PATH)
            # Ensure ingredient columns in recipes_df match self.ingredient_features
            self.recipe_vectors = self.recipes_df[self.ingredient_features].values
        except FileNotFoundError as e:
            print(f"Error loading data file: {e}. Make sure research notebook generated files.")
            raise
        except Exception as e:
            print(f"Error initializing NutritionApp: {e}")
            raise

    def _preprocess_input(self, ingredients_list):
        """Converts a list of ingredient names into a feature vector."""
        # Create a zero vector with the same columns as the training data
        input_vector = pd.DataFrame(np.zeros((1, len(self.ingredient_features))),
                                   columns=self.ingredient_features)
        # Mark ingredients present in the input list as 1
        count = 0
        for ingredient in ingredients_list:
            # Basic normalization (lowercase, maybe strip whitespace)
            norm_ingredient = ingredient.lower().strip()
            if norm_ingredient in input_vector.columns:
                input_vector[norm_ingredient] = 1
                count += 1
            else:
                print(f"Warning: Ingredient '{ingredient}' not in known features, ignoring.")
        if count == 0:
            print("Warning: None of the input ingredients were recognized.")
            # Return None or raise error? Returning None might be safer downstream
            return None
        return input_vector # Return the DataFrame/numpy array expected by model

    def predict_rating_class(self, ingredients_list):
        """Predicts the rating class ('bad', 'so-so', 'great') for a list of ingredients."""
        input_vector = self._preprocess_input(ingredients_list)
        if input_vector is None:
            return "unknown" # Or handle appropriately

        try:
            prediction = self.model.predict(input_vector)
            return prediction[0] # predict returns an array
        except Exception as e:
            print(f"Error during prediction: {e}")
            return "error"

    def get_nutrition_info(self, ingredients_list):
        """Retrieves nutrition information (%DV) for a list of ingredients."""
        results = {}
        for ingredient in ingredients_list:
            norm_ingredient = ingredient.lower().strip()
            if norm_ingredient in self.nutrition_df.index:
                # Select non-null nutrient values for this ingredient
                nutrient_data = self.nutrition_df.loc[norm_ingredient].dropna()
                # Optional: Filter to only show >0% DV or format nicely
                results[ingredient] = nutrient_data.to_dict()
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

    # --- Bonus Part ---
    def generate_daily_menu(self):
        """Generates a sample daily menu (Breakfast, Lunch, Dinner)."""
        menu = {}
        # *** CRUCIAL ASSUMPTION: recipes_df needs a 'meal_type' column ***
        # This column should be created during research (Phase 1) by tagging recipes
        # (e.g., based on keywords: 'omelette'->breakfast, 'salad'->lunch, 'roast'->dinner)
        if 'meal_type' not in self.recipes_df.columns:
             return {"error": "Cannot generate menu. 'meal_type' column missing in recipe data."}

        for meal in ['breakfast', 'lunch', 'dinner']:
            # Filter recipes for the current meal type
            meal_recipes = self.recipes_df[self.recipes_df['meal_type'].str.lower() == meal]

            if meal_recipes.empty:
                menu[meal] = {"error": f"No recipes found for {meal}"}
                continue

            # Optional: Filter for higher rated recipes if desired
            # meal_recipes = meal_recipes[meal_recipes['rating'] >= 3.5]
            # if meal_recipes.empty: # Handle case where filtering leaves no recipes
            #     menu[meal] = {"error": f"No high-rated recipes found for {meal}"}
            #     continue

            # Select one random recipe from the filtered list
            selected_recipe = meal_recipes.sample(n=1).iloc[0]

            # Get ingredients (columns where value is 1 or >0)
            recipe_ingredients = [col for col in self.ingredient_features if selected_recipe[col] > 0]

            # Get nutrition info for these ingredients
            nutrition_info = self.get_nutrition_info(recipe_ingredients)

            menu[meal] = {
                'title': selected_recipe.get('title', 'N/A'),
                'rating': selected_recipe.get('rating', 'N/A'),
                'ingredients': recipe_ingredients,
                'nutrients': nutrition_info, # This will be nested dict per ingredient
                'url': selected_recipe.get('url', 'N/A')
            }

        return menu