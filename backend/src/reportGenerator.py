import pandas as pd
import torch

from transformers import BlipForConditionalGeneration, BlipProcessor
from PIL import Image
import os
import re


class ReportGenerator:
    def __init__(self, model="nathansutton/generate-cxr", processor="nathansutton/generate-cxr", device='cuda'):

        self.model = BlipForConditionalGeneration.from_pretrained(model).to(device)
        self.processor = BlipProcessor.from_pretrained(processor)

        if not torch.cuda.is_available() and device == 'cuda':
            print("Warning: CUDA is not available. Using CPU instead.")
            self.device = torch.device("cpu")
        else:
            self.device = device

        self.model.eval() # Ensure the model is in evaluation mode

    def generate_report(self, image_path, indication, image_type="unknown"):
        """
        Generates a findings and impression report for a given image and indication.

        Args:
            image_filename (str): Path to the image.
            indication (str): The patient's indication.
            image_type (str): Type of image (e.g., "Frontal", "Lateral"). Used for logging.

        Returns:
            tuple: A tuple containing the generated findings and impression.
                   Returns ("FILE_NOT_FOUND", "FILE_NOT_FOUND") if the file doesn't exist.
                   Returns ("ERROR", "ERROR") if an error occurs during processing.
        """
        generated_findings = ""
        generated_impression = ""

        try:
            if os.path.exists(image_path):
                img = Image.open(image_path).convert("RGB")
                inputs = self.processor(images=img, text="indication: " + str(indication), return_tensors="pt").to(self.device)
                output = self.model.generate(**inputs, max_length=100)
                report_text = self.processor.decode(output[0], skip_special_tokens=True).strip()

                find_match = re.search(r"findings\s*:\s*(.*?)\s*impression\s*:", report_text, re.IGNORECASE)
                imp_match = re.search(r"impression\s*:\s*(.*)", report_text, re.IGNORECASE)

                generated_findings = find_match.group(1).strip() if find_match else ""
                generated_impression = imp_match.group(1).strip() if imp_match else ""

            else:
                print(f"  {image_type} Image file not found: {image_path}")
                return "FILE_NOT_FOUND", "FILE_NOT_FOUND"

        except Exception as e:
            print(f"  Error processing {image_type} image {image_path}: {e}")
            return "ERROR", "ERROR"

        return generated_findings, generated_impression