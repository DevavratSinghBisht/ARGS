import torch
from transformers import pipeline

class ClinicalTextSummarizer:
    def __init__(self, model_name="sshleifer/distilbart-cnn-12-6"):
        """
        Initializes the ClinicalTextSummarizer with a Hugging Face model.

        Args:
            model_name (str): The name of the pre-trained model to use.
                              Defaults to "microsoft/BiomedNLP-PubMedBERT-base-abstract-uncased".
        """
        self.summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6", device=0 if torch.cuda.is_available() else -1) # Use GPU if available

    def summarize(self, text, min_length=0, max_length=80):
        """
        Summarizes the input clinical text.

        Args:
            text (str): The clinical text to summarize.
            min_length (int): Minimum length of the summary.
            max_length (int): Maximum length of the summary.

        Returns:
            str: The summarized text.
        """
        if not text:
            return ""
        # Hugging Face pipeline expects a list of strings
        summary = self.summarizer(text, min_length=min_length, max_length=max_length, do_sample=True)[0]['summary_text']
        return summary