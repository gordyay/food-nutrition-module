#!/usr/bin/env python3

import argparse
import sys
from recipes import NutritionApp # Assuming recipes.py is in the same directory or PYTHONPATH

def format_nutrition(nutrition_data):
    """Formats the nested nutrition dictionary for printing."""
    output = []
    for ingredient, nutrients in nutrition_data.items():
        output.append(f"{ingredient.capitalize()}")
        if isinstance(nutrients, dict) and "error" not in nutrients:
            details = [f"- {name.replace('_', ' ').title()}: {value:.1f}% of Daily Value"
                       for name, value in nutrients.items() if value > 0] # Show only >0%
            if details:
                 output.extend(details)
            else:
                 output.append("- No significant nutrients found or data unavailable.")
        elif isinstance(nutrients, dict) and "error" in nutrients:
             output.append(f"- Error: {nutrients['error']}")
        else:
            output.append("- Nutrition data format unexpected.")
        output.append("...") # Separator between ingredients
    # Remove last separator if it exists
    if output and output[-1] == "...":
        output.pop()
    return "\n".join(output)




def main():
    parser = argparse.ArgumentParser(description='Food and Nutrition Assistant.')
    parser.add_argument('ingredients', nargs='?', default=None, # Make ingredients optional
                        help='Comma-separated list of ingredients (e.g., "milk,honey,jam")')

    args = parser.parse_args()

    if args.ingredients is None:
        parser.error("Please provide a list of ingredients ")


    try:
        app = NutritionApp()
    except Exception as e:
        print(f"Failed to initialize the application: {e}", file=sys.stderr)
        sys.exit(1)
    ingredients_list = [s.strip() for s in args.ingredients.split(',') if s.strip()]
    if not ingredients_list:
        print("Error: No valid ingredients provided.", file=sys.stderr)
        sys.exit(1)

    print(f"Analyzing ingredients: {', '.join(ingredients_list)}\n")

    # 1. Forecast Rating
    print("I. OUR FORECAST")
    rating_class = app.predict_rating_class(ingredients_list)
    if rating_class == 0:
        print("You might find it tasty, but in our opinion, it is a bad idea to have a")
        print("dish with that list of ingredients.")
    elif rating_class == 1:
        print("This combination seems okay, potentially a so-so dish.")
    elif rating_class == 2:
        print("This looks promising! It might be a great dish.")
    elif rating_class == 'unknown':
            print("Could not make a prediction. Input ingredients might not be recognized.")
    else: # Handle 'error' case
            print(f"An error occurred during prediction. the prediction is {rating_class}")
    print("\n")


    # 2. Nutrition Facts
    print("II. NUTRITION FACTS")
    nutrition_info = app.get_nutrition_info(ingredients_list)
    print(format_nutrition(nutrition_info))
    print("\n")


    # 3. Similar Recipes
    print("III. TOP-3 SIMILAR RECIPES:")
    similar_recipes = app.find_similar_recipes(ingredients_list, n=3)
    if similar_recipes:
        for recipe in similar_recipes:
            print(f"- {recipe.get('title', 'N/A')}, rating: {recipe.get('rating', 'N/A')}, URL:")
            print(f"  {recipe.get('url', 'N/A')}")
    else:
        print("No similar recipes found or an error occurred.")

if __name__ == '__main__':
    main()