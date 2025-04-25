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

def format_menu(menu_data):
    """Formats the daily menu dictionary for printing."""
    output = []
    for meal, details in menu_data.items():
        output.append(meal.upper())
        output.append("---------------------")
        if isinstance(details, dict) and "error" not in details:
             output.append(f"{details.get('title', 'N/A')} (rating: {details.get('rating', 'N/A')})")
             output.append("Ingredients:")
             output.extend([f"- {ing}" for ing in details.get('ingredients', [])])
             output.append("Nutrients (per ingredient):")
             # Reformat nested nutrition slightly for menu context
             for ing, nutrients in details.get('nutrients', {}).items():
                 output.append(f"  {ing.capitalize()}:")
                 if isinstance(nutrients, dict) and "error" not in nutrients:
                      ing_details = [f"  - {name.replace('_', ' ').title()}: {value:.1f}% DV"
                                     for name, value in nutrients.items() if value > 0]
                      if ing_details:
                           output.extend(ing_details)
                      else:
                           output.append("  - No significant nutrients tracked.")
                 else:
                      output.append(f"  - {nutrients.get('error', 'Data unavailable')}")

             output.append(f"URL: {details.get('url', 'N/A')}")
        else:
             output.append(f"Error generating {meal}: {details.get('error', 'Unknown error')}")
        output.append("\n") # Space between meals
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description='Food and Nutrition Assistant.')
    parser.add_argument('ingredients', nargs='?', default=None, # Make ingredients optional
                        help='Comma-separated list of ingredients (e.g., "milk,honey,jam"). Required unless --menu is used.')
    parser.add_argument('--menu', action='store_true', # Add bonus flag
                        help='Generate a sample daily menu instead of analyzing ingredients.')

    args = parser.parse_args()

    # Validate input: need either ingredients or --menu
    if not args.menu and args.ingredients is None:
        parser.error("Please provide a list of ingredients or use the --menu flag.")
    if args.menu and args.ingredients is not None:
        parser.error("Cannot use --menu flag together with an ingredient list.")

    try:
        app = NutritionApp()
    except Exception as e:
        print(f"Failed to initialize the application: {e}", file=sys.stderr)
        sys.exit(1)

    if args.menu:
        # --- Bonus Part Execution ---
        print("GENERATING DAILY MENU...")
        daily_menu = app.generate_daily_menu()
        if "error" in daily_menu and len(daily_menu) == 1: # Check for top-level error
            print(f"\nError: {daily_menu['error']}")
        else:
            print(format_menu(daily_menu))

    else:
        # --- Mandatory Part Execution ---
        ingredients_list = [s.strip() for s in args.ingredients.split(',') if s.strip()]
        if not ingredients_list:
            print("Error: No valid ingredients provided.", file=sys.stderr)
            sys.exit(1)

        print(f"Analyzing ingredients: {', '.join(ingredients_list)}\n")

        # 1. Forecast Rating
        print("I. OUR FORECAST")
        rating_class = app.predict_rating_class(ingredients_list)
        if rating_class == 'bad':
            print("You might find it tasty, but in our opinion, it is a bad idea to have a")
            print("dish with that list of ingredients.")
        elif rating_class == 'so-so':
            print("This combination seems okay, potentially a so-so dish.")
        elif rating_class == 'great':
            print("This looks promising! It might be a great dish.")
        elif rating_class == 'unknown':
             print("Could not make a prediction. Input ingredients might not be recognized.")
        else: # Handle 'error' case
             print("An error occurred during prediction.")
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