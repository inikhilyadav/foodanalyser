!pip install pyzbar -q
!apt-get update -qq
!apt-get install -y libzbar0 -qq
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
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)
