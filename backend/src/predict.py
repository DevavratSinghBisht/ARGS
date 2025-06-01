import os
from typing import List, Dict, Any
from reportGenerator import ReportGenerator
from cheXpert import CheXpert
from summarizer import ClinicalTextSummarizer

from utils import (get_summary_params, 
                   replace_indication_placeholder, 
                   aggregate_chexpert_predictions, 
                   chexpert_preds_to_text, 
                   get_largest_image)

def getPrediction(data: List[Dict[str, str]], report_generator: ReportGenerator, chexpert: CheXpert, summarizer: ClinicalTextSummarizer) -> List[Dict[str, Any]]:
    """
    Processes chest X-ray data to generate summarized findings and impressions.

    Args:
        data (list): List of dictionaries, each representing a patient entry
                     with uid, image paths, and indications (as per contract).
        report_generator (ReportGenerator): An instance of the ReportGenerator class.
        chexpert (CheXpert): An instance of the CheXpert class.
        summarizer (ClinicalTextSummarizer): An instance of the ClinicalTextSummarizer class.

    Returns:
        list: List of dictionaries, each with uid, generated findings, and impression.
              Returns 'N/A' for findings/impression if no relevant images are found or
              processing fails.
    """
    results = []

    for data_point in data:
        uid = data_point.get('uid', 'UnknownUID')
        frontal_images = data_point.get('frontal_images', [])
        lateral_images = data_point.get('lateral_images', [])
        indication = data_point.get('indications', '')
        indication = replace_indication_placeholder(indication, "")

        final_findings = ""
        final_impression = ""


        # 1 Find Pathologies using Chexpert
        chex_preds = []

        for img in frontal_images:
            chex_preds.append(chexpert.analyze_image(img))

        for img in lateral_images:
            chex_preds.append(chexpert.analyze_image(img))

        chex_aggreated_preds = aggregate_chexpert_predictions(chex_preds)
        chex_text = chexpert_preds_to_text(chex_aggreated_preds)

        print("CHEX", chex_text)
        print("-"*20)

        # 2. Generate Frontal and Lateral Findings
        if frontal_images:
            # Find largest frontal image
            largest_frontal_image_path = get_largest_image(frontal_images)

            if largest_frontal_image_path and os.path.exists(largest_frontal_image_path):

                fron_gen_findings, fron_gen_impression = report_generator.generate_report(
                    largest_frontal_image_path, indication, "Frontal"
                )
                print(f"Frontal Findings {fron_gen_findings}, impression {fron_gen_impression}")
                print("-"*20)

            else:
                 print(f"Warning: No valid frontal image found for UID {uid} among paths: {frontal_images}")


        if lateral_images:
            # Find largest lateral image
            largest_lateral_image_path = get_largest_image(lateral_images)

            if largest_lateral_image_path and os.path.exists(largest_lateral_image_path):

                # 2. Use largest image and indication with report generator
                lat_gen_findings, lat_gen_impression = report_generator.generate_report(
                    largest_lateral_image_path, indication, "Lateral"
                )
                print(f"Lateral Findings {lat_gen_findings}, impression {lat_gen_impression}")
                print("-"*20)

            else:
                 print(f"Warning: No valid lateral image found for UID {uid} among paths: {lateral_images}")


        # 3. Summarize findings and impressions (combining generated and CheXpert text)
        findings_combined_text = ""
        if fron_gen_findings != "":
            findings_combined_text += f"{fron_gen_findings}. \n"
        if lat_gen_findings != "":
            findings_combined_text += f"{lat_gen_findings}. \n"
        if chex_text != "":
            findings_combined_text += f"Pathologies Found are {chex_text}. \n"

        print("Findings_combined: ", findings_combined_text)

        findings_summary_params = get_summary_params(findings_combined_text)
        min_findings_length = findings_summary_params["min_length"]
        max_findings_length = findings_summary_params["max_length"]
        final_findings = summarizer.summarize(findings_combined_text, min_findings_length, max_findings_length)

        impression_combined_text = ""
        if fron_gen_impression != "":
            impression_combined_text += f"{fron_gen_impression}. \n"
        if lat_gen_impression != "":
            impression_combined_text += f"{lat_gen_impression}. \n"
        if chex_text != "":
            impression_combined_text += f"Pathologies Found are {chex_text}. \n"

        print("Impression_combined: ", impression_combined_text)

        impression_summary_params = get_summary_params(impression_combined_text)
        min_impression_length = impression_summary_params["min_length"]
        max_impression_length = impression_summary_params["max_length"]
        final_impression = summarizer.summarize(impression_combined_text, min_impression_length, max_impression_length)

        # Combine findings and impressions (this is a simple concatenation, could be more complex)
        # Since the contract asks for 'findings' and 'impression' for the UID, we can combine
        # the summarized results from frontal and lateral views if both exist.
        # If only one view exists, use that view's summary.
        # final_findings = ""
        # final_impression = ""

        # if frontal_findings != "N/A" and lateral_findings != "N/A":
        #     final_findings = f"Frontal Findings: {frontal_findings} Lateral Findings: {lateral_findings}"
        #     final_impression = f"Frontal Impression: {frontal_impression} Lateral Impression: {lateral_impression}"
        # elif frontal_findings != "N/A":
        #     final_findings = frontal_findings
        #     final_impression = frontal_impression
        # elif lateral_findings != "N/A":
        #     final_findings = lateral_findings
        #     final_impression = lateral_impression
        # else:
        #      final_findings = "No image data found for analysis."
        #      final_impression = "No image data found for analysis."


        results.append({
            'uid': uid,
            'findings': final_findings,
            'impression': final_impression
        })

    return results