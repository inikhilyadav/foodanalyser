import gradio as gr
import requests
import matplotlib.pyplot as plt
import numpy as np
from pyzbar.pyzbar import decode
import cv2
from typing import Optional, Tuple, List
import os

# -------------------------------------------------------------------
# 1. Open Food Facts API
# -------------------------------------------------------------------
def get_product(barcode: str) -> Optional[dict]:
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    headers = {
        "User-Agent": "FoodHealthAnalyzer/1.0 (Student Project; contact@example.com)"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        data = response.json()
        if data.get("status") != 1:
            return None
        return data["product"]
    except Exception:
        return None

# -------------------------------------------------------------------
# 2. Health Analysis Engine
# -------------------------------------------------------------------
def analyze_product(product: dict) -> dict:
    nutriments = product.get("nutriments", {})

    sugar = nutriments.get("sugars_100g", 0) or 0
    fat = nutriments.get("fat_100g", 0) or 0
    sat_fat = nutriments.get("saturated-fat_100g", 0) or 0
    salt = nutriments.get("salt_100g", 0) or 0
    sodium = nutriments.get("sodium_100g", 0) or 0
    protein = nutriments.get("proteins_100g", 0) or 0
    fiber = nutriments.get("fiber_100g", 0) or 0

    nutri_score = product.get("nutriscore_grade") or "unknown"
    nova_group = product.get("nova_group")

    score = 100
    reasons = []

    if sugar > 15:
        score -= 20
        reasons.append("High sugar content")
    elif sugar > 8:
        score -= 10
        reasons.append("Moderate sugar")

    if fat > 20:
        score -= 15
        reasons.append("High fat")

    if sat_fat > 5:
        score -= 15
        reasons.append("High saturated fat")

    if salt > 1.5:
        score -= 20
        reasons.append("High salt")

    if sodium > 0.6:
        score -= 10
        reasons.append("High sodium")

    if nova_group == 4:
        score -= 15
        reasons.append("Ultra-processed food (NOVA 4)")
    elif nova_group == 3:
        score -= 5
        reasons.append("Processed food (NOVA 3)")

    if protein >= 10:
        score += 5
        reasons.append("Good protein source")

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

# -------------------------------------------------------------------
# 3. Recommendation Engine
# -------------------------------------------------------------------
def recommendation_engine(score: int, sugar: float, salt: float,
                         calories: float, protein: float, fiber: float) -> Tuple[str, List[str]]:
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

# -------------------------------------------------------------------
# 4. Ingredient / Allergen / NOVA Analysis
# -------------------------------------------------------------------
NOVA_LABELS = {
    1: "Unprocessed or minimally processed",
    2: "Processed culinary ingredient",
    3: "Processed food",
    4: "Ultra-processed food"
}

def clean_tag(tag: str) -> str:
    return tag.split(":")[-1].replace("-", " ").title()

def analyze_ingredients(product: dict) -> dict:
    nova_group = product.get("nova_group")
    nova_label = NOVA_LABELS.get(nova_group, "Not classified")

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

# -------------------------------------------------------------------
# 5. Barcode Scanner
# -------------------------------------------------------------------
def scan_barcode(image: np.ndarray) -> Optional[str]:
    if image is None:
        return None
    img_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    detected = decode(img_bgr)
    if not detected:
        return None
    barcode_data = detected[0].data.decode("utf-8").strip()
    return barcode_data

# -------------------------------------------------------------------
# 6. Main Food Analyzer
# -------------------------------------------------------------------
def food_analyzer(barcode: str):
    try:
        product = get_product(barcode.strip())
        if product is None:
            return (
                "❌ Product not found. Check the barcode or try another.",
                None,
                None,
                "Failed"
            )

        name = product.get("product_name", "Unknown")
        brand = product.get("brands", "Unknown")

        analysis = analyze_product(product)
        ingredient_info = analyze_ingredients(product)

        score = analysis["Health Score"]
        status = analysis["Recommendation"]
        reasons = analysis["Reasons"]

        nova_group = ingredient_info["NOVA Group"]
        nova_display = f"NOVA {nova_group}: {ingredient_info['NOVA Label']}" if nova_group else ingredient_info["NOVA Label"]

        allergen_display = ", ".join(ingredient_info["Allergens"]) if ingredient_info["Allergens"] else "None declared"

        report = f"""
🥗 FOOD HEALTH REPORT
==========================
Product: {name}
Brand: {brand}
Health Score: {score}/100
Recommendation: {status}
Processing Level: {nova_display}
⚠️ Allergens: {allergen_display}
"""
        if ingredient_info["Traces"]:
            report += f"\nMay contain traces of: {', '.join(ingredient_info['Traces'])}\n"
        if ingredient_info["Additives"]:
            report += f"\nAdditives ({ingredient_info['Additive Count']}): {', '.join(ingredient_info['Additives'])}\n"

        report += "\nWarnings:"
        if reasons:
            for w in reasons:
                report += f"\n⚠️ {w}"
        else:
            report += "\nNo major issues detected"

        n = product.get("nutriments", {})
        sugar = n.get("sugars_100g", 0) or 0
        salt = n.get("salt_100g", 0) or 0
        calories = n.get("energy-kcal_100g", 0) or 0
        protein = n.get("proteins_100g", 0) or 0
        fiber = n.get("fiber_100g", 0) or 0

        rec_status, rec_advice = recommendation_engine(score, sugar, salt, calories, protein, fiber)
        report += f"\n\n💡 Detailed Advice ({rec_status}):"
        for adv in rec_advice:
            report += f"\n• {adv}"

        image = product.get("image_front_url", None)

        nutrients = {
            "Sugar": sugar,
            "Fat": n.get("fat_100g", 0) or 0,
            "Protein": protein,
            "Fiber": fiber,
            "Salt": salt
        }
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(nutrients.keys(), nutrients.values(),
               color=["red", "orange", "green", "blue", "purple"])
        ax.set_title("Nutrition per 100g")
        ax.set_ylabel("Amount (grams)")
        plt.xticks(rotation=45)
        plt.tight_layout()

        return report, image, fig, "✅ Analysis completed"

    except Exception as e:
        return (
            f"❌ Error: {str(e)}",
            None,
            None,
            "Failed"
        )

# -------------------------------------------------------------------
# 7. Build Gradio UI
# -------------------------------------------------------------------
with gr.Blocks(theme=gr.themes.Soft(), title="Food Health Analyzer") as demo:
    gr.Markdown("# 🥗 Food Health Analyzer")
    gr.Markdown("Enter a food barcode manually **or** upload an image of the package to scan it automatically.")

    with gr.Tabs():
        with gr.TabItem("🔢 Manual Entry"):
            with gr.Row():
                barcode_input = gr.Textbox(
                    label="Enter Barcode",
                    placeholder="Example: 3017620422003 (Nutella)",
                    scale=3
                )
                analyze_btn = gr.Button("🔍 Analyze", variant="primary", scale=1)

            status_manual = gr.Textbox(label="Status", value="Ready", interactive=False)

            with gr.Tabs():
                with gr.TabItem("📋 Report"):
                    report_manual = gr.Textbox(label="Food Report", lines=22, interactive=False)
                with gr.TabItem("🖼️ Product Image"):
                    image_manual = gr.Image(label="Product Image", type="filepath")
                with gr.TabItem("📊 Nutrient Chart"):
                    plot_manual = gr.Plot(label="Nutrient Chart")

            gr.Examples(
                examples=["3017620422003", "5449000131805", "737628064502"],
                inputs=barcode_input,
                label="Try these barcodes"
            )

        with gr.TabItem("📸 Scan Barcode"):
            with gr.Row():
                image_input = gr.Image(label="Upload package image", type="numpy")
                with gr.Column():
                    scan_status = gr.Textbox(label="Scan Status", value="Upload an image and click Detect", interactive=False)
                    detected_barcode = gr.Textbox(label="Detected Barcode", interactive=False)
                    with gr.Row():
                        detect_btn = gr.Button("🔍 Detect Barcode")
                        analyze_scanned_btn = gr.Button("📊 Analyze This Product", variant="primary")

            final_status = gr.Textbox(label="Status", value="Ready", interactive=False)

            with gr.Group(visible=False) as results_group:
                gr.Markdown("### 📊 Analysis Results")
                report_scan_visible = gr.Textbox(label="Food Report", lines=22, interactive=False)
                image_scan_visible = gr.Image(label="Product Image", type="filepath")
                plot_scan_visible = gr.Plot(label="Nutrient Chart")

    # Interactions
    analyze_btn.click(
        fn=food_analyzer,
        inputs=barcode_input,
        outputs=[report_manual, image_manual, plot_manual, status_manual]
    )
    barcode_input.submit(
        fn=food_analyzer,
        inputs=barcode_input,
        outputs=[report_manual, image_manual, plot_manual, status_manual]
    )

    def handle_detect(image):
        barcode = scan_barcode(image)
        if barcode:
            return f"✅ Barcode found: {barcode}", barcode
        else:
            return "❌ No barcode detected. Try another image.", ""

    detect_btn.click(
        fn=handle_detect,
        inputs=image_input,
        outputs=[scan_status, detected_barcode]
    )

    def handle_scan_analyze(barcode):
        report, img, plot, status = food_analyzer(barcode)
        return report, img, plot, status, gr.update(visible=True)

    analyze_scanned_btn.click(
        fn=handle_scan_analyze,
        inputs=detected_barcode,
        outputs=[report_scan_visible, image_scan_visible, plot_scan_visible, final_status, results_group]
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)
