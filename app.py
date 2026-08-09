!pip install requests
import requests

def get_product(barcode):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"

    headers = {
        "User-Agent": "FoodHealthAnalyzer/1.0 (Student Project; your_email@example.com)"
    }

    response = requests.get(url, headers=headers, timeout=10)

    print("Status Code:", response.status_code)

    if response.status_code != 200:
        print(response.text)
        return None

    data = response.json()

    if data.get("status") != 1:
        print("Product not found in Open Food Facts.")
        return None

    return data["product"]

# ----------------------------
# Health Analysis Engine
# ----------------------------
def analyze_product(product):


    nutriments = product.get("nutriments", {})

    sugar = nutriments.get("sugars_100g", 0)
    fat = nutriments.get("fat_100g", 0)
    sat_fat = nutriments.get("saturated-fat_100g", 0)
    salt = nutriments.get("salt_100g", 0)
    sodium = nutriments.get("sodium_100g", 0)
    protein = nutriments.get("proteins_100g", 0)
    fiber = nutriments.get("fiber_100g", 0)
    calories = nutriments.get("energy-kcal_100g", 0)

    nutri_score = product.get("nutriscore_grade") or "unknown"
    nova_group = product.get("nova_group")

    score = 100
    reasons = []

    # Sugar
    if sugar > 15:
        score -= 20
        reasons.append("High sugar content")
    elif sugar > 8:
        score -= 10
        reasons.append("Moderate sugar")

    # Fat
    if fat > 20:
        score -= 15
        reasons.append("High fat")

    # Saturated Fat
    if sat_fat > 5:
        score -= 15
        reasons.append("High saturated fat")

    # Salt
    if salt > 1.5:
        score -= 20
        reasons.append("High salt")

    # Sodium
    if sodium > 0.6:
        score -= 10
        reasons.append("High sodium")

    # NOVA processing group (1 = unprocessed, 4 = ultra-processed)
    if nova_group == 4:
        score -= 15
        reasons.append("Ultra-processed food (NOVA 4)")
    elif nova_group == 3:
        score -= 5
        reasons.append("Processed food (NOVA 3)")

    # Protein Bonus
    if protein >= 10:
        score += 5
        reasons.append("Good protein source")

    # Fiber Bonus
    if fiber >= 5:
        score += 10
        reasons.append("High fiber")

    score = max(0, min(score, 100))

    if score >= 80:
        recommendation = "✅ Recommended"
    elif score >= 60:
        recommendation = "🟡 Consume in Moderation"
    else:
        recommendation = "❌ Avoid Frequent Consumption"

    return {
        "Health Score": score,
        "Recommendation": recommendation,
        "Reasons": reasons,
        "NutriScore": nutri_score.upper()
    }


# ----------------------------
# Recommendation Engine
# ----------------------------
def recommendation_engine(score, sugar, salt, calories, protein, fiber):

    recommendations = []

    if score >= 80:
        status = "🟢 Recommended"
    elif score >= 60:
        status = "🟡 Consume in Moderation"
    else:
        status = "🔴 Avoid Frequent Consumption"

    if sugar > 15:
        recommendations.append("High sugar. Not suitable for diabetic individuals.")

    if salt > 1.5:
        recommendations.append("High salt. Limit intake if you have hypertension.")

    if calories > 400:
        recommendations.append("High in calories. Consume in moderation.")

    if protein >= 10:
        recommendations.append("Good source of protein.")

    if fiber >= 5:
        recommendations.append("High fiber content supports digestive health.")

    return status, recommendations
# ----------------------------
# Ingredient / Allergen / NOVA Analysis
# ----------------------------
# Uses fields Open Food Facts already returns on every product:
#   nova_group                -> processing level, 1 (minimal) - 4 (ultra-processed)
#   allergens_tags            -> declared allergens, e.g. "en:milk"
#   traces_tags                -> "may contain traces of"
#   additives_tags             -> E-number additives
#   ingredients_analysis_tags -> vegan / vegetarian / palm-oil flags

NOVA_LABELS = {
    1: "Unprocessed or minimally processed",
    2: "Processed culinary ingredient",
    3: "Processed food",
    4: "Ultra-processed food"
}

def clean_tag(tag):
    # OFF tags look like "en:milk" -> "Milk"
    return tag.split(":")[-1].replace("-", " ").title()

def analyze_ingredients(product):

    nova_group = product.get("nova_group")
    nova_label = NOVA_LABELS.get(nova_group, "Not classified by Open Food Facts")

    allergens_raw = product.get("allergens_tags") or []
    allergens = sorted({clean_tag(a) for a in allergens_raw})

    traces_raw = product.get("traces_tags") or []
    traces = sorted({clean_tag(t) for t in traces_raw})

    additives_raw = product.get("additives_tags") or []
    additives = sorted({clean_tag(a) for a in additives_raw})

    analysis_tags = product.get("ingredients_analysis_tags") or []
    palm_oil_free = "en:palm-oil-free" in analysis_tags
    contains_palm_oil = "en:palm-oil" in analysis_tags
    vegan = "en:vegan" in analysis_tags
    vegetarian = vegan or ("en:vegetarian" in analysis_tags)

    ingredients_text = (product.get("ingredients_text") or "").strip()

    return {
        "NOVA Group": nova_group,
        "NOVA Label": nova_label,
        "Allergens": allergens,
        "Traces": traces,
        "Additives": additives,
        "Additive Count": len(additives),
        "Palm Oil Free": palm_oil_free,
        "Contains Palm Oil": contains_palm_oil,
        "Vegan": vegan,
        "Vegetarian": vegetarian,
        "Ingredients Text": ingredients_text
    }
# ----------------------------
# Display Product Information
# ----------------------------
def display_product(product):

    print("=" * 60)

    print("Product Name :", product.get("product_name", "Unknown"))
    print("Brand        :", product.get("brands", "Unknown"))
    print("Quantity     :", product.get("quantity", "Unknown"))
    print("Countries    :", product.get("countries", "Unknown"))

    nutriments = product.get("nutriments", {})

    print("\nNutrition (per 100g)")
    print("----------------------------")
    print("Calories      :", nutriments.get("energy-kcal_100g", "N/A"))
    print("Sugar         :", nutriments.get("sugars_100g", "N/A"), "g")
    print("Fat           :", nutriments.get("fat_100g", "N/A"), "g")
    print("Sat. Fat      :", nutriments.get("saturated-fat_100g", "N/A"), "g")
    print("Protein       :", nutriments.get("proteins_100g", "N/A"), "g")
    print("Fiber         :", nutriments.get("fiber_100g", "N/A"), "g")
    print("Salt          :", nutriments.get("salt_100g", "N/A"), "g")

    ingredient_info = analyze_ingredients(product)

    print("\nProcessing Level (NOVA)")
    print("----------------------------")
    if ingredient_info["NOVA Group"]:
        print(f"NOVA {ingredient_info['NOVA Group']}: {ingredient_info['NOVA Label']}")
    else:
        print(ingredient_info["NOVA Label"])

    print("\nAllergens")
    print("----------------------------")
    print(", ".join(ingredient_info["Allergens"]) if ingredient_info["Allergens"] else "None declared")
    if ingredient_info["Traces"]:
        print("May contain traces of:", ", ".join(ingredient_info["Traces"]))

    print("\nAdditives (E-numbers)")
    print("----------------------------")
    if ingredient_info["Additives"]:
        print(f"{ingredient_info['Additive Count']} additive(s):", ", ".join(ingredient_info["Additives"]))
    else:
        print("None declared")

    print("=" * 60)
# ----------------------------
# Main Program
# ----------------------------

barcode = input("Enter Product Barcode: ")

product = get_product(barcode)

if product is None:
    print("Product not found.")
else:

    display_product(product)

    result = analyze_product(product)


    print("\nHEALTH ANALYSIS")
    print("-" * 30)
    print("NutriScore      :", result["NutriScore"])
    print("Health Score    :", result["Health Score"], "/100")
    print("Recommendation  :", result["Recommendation"])

    print("\nReasons")
    for r in result["Reasons"]:
        print("•", r)

nutriments = product.get("nutriments", {})

status, advice = recommendation_engine(
    score=result["Health Score"],
    sugar=nutriments.get("sugars_100g", 0),
    salt=nutriments.get("salt_100g", 0),
    calories=nutriments.get("energy-kcal_100g", 0),
    protein=nutriments.get("proteins_100g", 0),
    fiber=nutriments.get("fiber_100g", 0)
)
print("\nRECOMMENDATION")
print("-" * 30)
print(status)

print("\nAdvice:")
for item in advice:
    print("•", item)
# ----------------------------
# Quick connectivity test (optional)
# ----------------------------
import requests

headers = {"User-Agent": "FoodHealthAnalyzer/1.0 (Student Project)"}

response = requests.get(
    "https://world.openfoodfacts.org/api/v0/product/3017620422003.json",
    headers=headers
)

print(response.status_code)
print(response.text[:200])
from IPython.display import Image, display

image = product.get("image_front_url")

if image:
    display(Image(url=image))
import matplotlib.pyplot as plt

labels = ["Sugar", "Fat", "Protein", "Fiber", "Salt"]

values = [
    nutriments.get("sugars_100g", 0),
    nutriments.get("fat_100g", 0),
    nutriments.get("proteins_100g", 0),
    nutriments.get("fiber_100g", 0),
    nutriments.get("salt_100g", 0)
]

plt.figure(figsize=(7, 4))

plt.bar(
    labels,
    values,
    color=[
        "red",      # Sugar
        "orange",   # Fat
        "green",    # Protein
        "blue",     # Fiber
        "purple"    # Salt
    ]
)

plt.title("Nutrition per 100 g")
plt.ylabel("grams")
plt.show()
!pip install pyzbar -q

import cv2
import numpy as np
from pyzbar.pyzbar import decode

def scan_barcode(image):
    if image is None:
        return None

    # Convert Gradio image to OpenCV format
    img = np.array(image)

    # Make sure image is RGB/BGR compatible
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # Try to detect barcode
    detected = decode(img)

    if not detected:
        return None

    # Return first barcode found
    barcode = detected[0].data.decode("utf-8").strip()

    return barcode
import gradio as gr


import matplotlib.pyplot as plt


def food_analyzer(barcode):

    try:
        product = get_product(barcode)

        if product is None:
            return (
                "❌ Product not found",
                None,
                None,
                "Try another barcode"
            )


        name = product.get("product_name", "Unknown")
        brand = product.get("brands", "Unknown")


        analysis = analyze_product(product)
        ingredient_info = analyze_ingredients(product)


        score = analysis.get("Health Score", 0)
        status = analysis.get("Recommendation", "")
        warnings = analysis.get("Reasons", [])


        nova_group = ingredient_info["NOVA Group"]
        nova_display = f"NOVA {nova_group}: {ingredient_info['NOVA Label']}" if nova_group else ingredient_info["NOVA Label"]

        allergen_display = ", ".join(ingredient_info["Allergens"]) if ingredient_info["Allergens"] else "None declared"

        report = f"""

🥗 FOOD HEALTH REPORT
==========================

Product:
{name}

Brand:
{brand}

Health Score:
{score}/100

Recommendation:
{status}

Processing Level:
{nova_display}

⚠ Allergens:
{allergen_display}
"""

        if ingredient_info["Traces"]:
            report += f"\nMay contain traces of: {', '.join(ingredient_info['Traces'])}\n"

        if ingredient_info["Additives"]:
            report += f"\nAdditives ({ingredient_info['Additive Count']}): {', '.join(ingredient_info['Additives'])}\n"

        report += "\nWarnings:"

        if warnings:
            for w in warnings:
                report += f"\n⚠ {w}"
        else:
            report += "\nNo major issues detected"



        # Product Image

        image = product.get(
            "image_front_url",
            None
        )


        # -------- Nutrient Chart --------

        n = product.get(
            "nutriments",
            {}
        )


        nutrients = {
            "Sugar": n.get("sugars_100g",0),
            "Fat": n.get("fat_100g",0),
            "Protein": n.get("proteins_100g",0),
            "Fiber": n.get("fiber_100g",0),
            "Salt": n.get("salt_100g",0)
        }


        fig, ax = plt.subplots(
            figsize=(7,4)
        )

        ax.bar(
            nutrients.keys(),
            nutrients.values(),
            color=[
                "red",
                "orange",
                "green",
                "blue",
                "purple"
            ]
        )


        ax.set_title(
            "Nutrition per 100g"
        )

        ax.set_ylabel(
            "Amount (grams)"
        )

        plt.xticks(
            rotation=45
        )

        plt.tight_layout()



        return (
            report,
            image,
            fig,
            "✅ Analysis completed"
        )


    except Exception as e:

        return (
            f"Error: {e}",
            None,
            None,
            "Failed"
        )

# ============================================================
# FOOD HEALTH ANALYZER - 3 INPUT OPTIONS
# ============================================================

import gradio as gr


# ------------------------------------------------------------
# CAMERA ANALYZER
# ------------------------------------------------------------

def camera_analyzer(image):

    barcode = scan_barcode(image)

    if not barcode:
        return (
            "❌ No barcode detected.\n\n"
            "Please make sure the barcode is clearly visible.",
            None,
            None,
            "❌ Barcode not detected"
        )

    report, product_image, chart, status = food_analyzer(barcode)

    return (
        report,
        product_image,
        chart,
        f"📷 Barcode detected: {barcode}\n\n{status}"
    )


# ------------------------------------------------------------
# TEXT / SEARCH ANALYZER
# ------------------------------------------------------------

def search_analyzer(barcode):

    barcode = str(barcode).strip()

    if not barcode:
        return (
            "❌ Please enter a barcode.",
            None,
            None,
            "Waiting for barcode..."
        )

    report, product_image, chart, status = food_analyzer(barcode)

    return (
        report,
        product_image,
        chart,
        f"🔎 Barcode searched: {barcode}\n\n{status}"
    )


# ------------------------------------------------------------
# IMAGE UPLOAD ANALYZER
# ------------------------------------------------------------

def upload_analyzer(image):

    barcode = scan_barcode(image)

    if not barcode:
        return (
            "❌ No barcode detected in the uploaded image.\n\n"
            "Please upload a clearer image where the barcode is visible.",
            None,
            None,
            "❌ Barcode not detected"
        )

    report, product_image, chart, status = food_analyzer(barcode)

    return (
        report,
        product_image,
        chart,
        f"🖼️ Barcode detected: {barcode}\n\n{status}"
    )


# ============================================================
# GRADIO UI
# ============================================================

with gr.Blocks(
    title="Food Health Analyzer"
) as interface:

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    gr.Markdown(
        """
        # 🥗 Food Health Analyzer

        ### Check your food before you eat it

        Choose how you want to identify your product.
        """
    )

    # --------------------------------------------------------
    # INPUT METHOD
    # --------------------------------------------------------

    gr.Markdown(
        """
        ## 🔍 How would you like to identify the product?
        """
    )

    with gr.Tabs():

      # ====================================================
        # OPTION 1 - CAMERA
        # ====================================================

        with gr.Tab("📷 Scan Barcode"):

            gr.Markdown(
                """
                ### 📷 Scan using your camera

                Point your camera at the product barcode.
                """
            )

            with gr.Row():

                camera_input = gr.Image(
                    sources=["webcam"],
                    type="numpy",
                    label="Camera"
                )

                with gr.Column():

                    camera_scan_button = gr.Button(
                        "🔍 Scan & Analyze",
                        variant="primary"
                    )

                    camera_status = gr.Textbox(
                        label="Scanner Status",
                        lines=3
                    )


        # ====================================================
        # OPTION 2 - TYPE BARCODE
        # ====================================================

        with gr.Tab("🔎 Type / Search"):

            gr.Markdown(
                """
                ### 🔎 Enter the barcode manually

                Type the barcode printed on the product package.
                """
            )

            barcode_input = gr.Textbox(
                label="Barcode",
                placeholder="Example: 3017620422003",
                info="Enter the product barcode"
            )

            search_button = gr.Button(
                "🔎 Search & Analyze",
                variant="primary"
            )

            search_status = gr.Textbox(
                label="Search Status",
                lines=3
            )


        # ====================================================
        # OPTION 3 - UPLOAD IMAGE
        # ====================================================

        with gr.Tab("🖼️ Upload Image"):

            gr.Markdown(
                """
                ### 🖼️ Upload a product image

                Upload a photo where the barcode is clearly visible.
                """
            )

            upload_input = gr.Image(
                type="numpy",
                sources=["upload"],
                label="Upload Product / Barcode Image"
            )

            upload_button = gr.Button(
                "🖼️ Analyze Image",
                variant="primary"
            )

            upload_status = gr.Textbox(
                label="Image Status",
                lines=3
            )


    # ========================================================
    # RESULTS
    # ========================================================

    gr.Markdown(
        """
        ---
        ## 📊 Food Safety Report
        """
    )

    report_output = gr.Textbox(
        label="🥗 Analysis",
        lines=25
    )

    with gr.Row():

        product_image_output = gr.Image(
            label="📦 Product Image"
        )

        nutrition_chart_output = gr.Plot(
            label="📊 Nutrition per 100g"

        )



    # ========================================================
    # BUTTON CONNECTIONS
    # ========================================================

    # Camera
    camera_scan_button.click(
        fn=camera_analyzer,
        inputs=camera_input,
        outputs=[
            report_output,
            product_image_output,
            nutrition_chart_output,
            camera_status
        ]
    )


    # Manual barcode
    search_button.click(
        fn=search_analyzer,
        inputs=barcode_input,
        outputs=[
            report_output,
            product_image_output,
            nutrition_chart_output,
            search_status
        ]
    )


    # Uploaded image
    upload_button.click(
        fn=upload_analyzer,
        inputs=upload_input,
        outputs=[
            report_output,
            product_image_output,
            nutrition_chart_output,
            upload_status
        ]
    )


    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    gr.Markdown(
        """
        ---

        **Food Safety Pipeline**

        📷 / 🔎 / 🖼️
        → Barcode
        → Product Lookup
        → Nutrition
        → NOVA
        → Allergens
        → Additives
        → Health Score
        """
    )


# ============================================================
# LAUNCH
# ============================================================

interface.launch(share=True)

# NOTE: Colab embeds this app in a restricted iframe that blocks camera
# access, so the webcam tab will show nothing clickable if opened inline.
# Click the public https://....gradio.live link printed above and open
# it in its own browser tab - the camera tab works normally there.
# (Upload and manual search work fine either way.)
