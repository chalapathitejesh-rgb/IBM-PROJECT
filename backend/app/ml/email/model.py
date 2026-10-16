import torch
import torch.nn as nn
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import shap
import numpy as np

class PhishingEmailDetector(nn.Module):
    def __init__(self, device='cpu'):
        super().__init__()
        self.device = device
        
        # Using a fast DistilBERT model. 
        # In production, this would be a model fine-tuned on Enron+Phishing datasets.
        model_name = "distilbert-base-uncased"
        self.tokenizer = DistilBertTokenizer.from_pretrained(model_name)
        self.model = DistilBertForSequenceClassification.from_pretrained(
            model_name, 
            num_labels=2 # 0: Legitimate, 1: Phishing
        )
        
        self.to(self.device)
        self.eval()
        
    def predict(self, text: str):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
        # Probability of class 1 (Phishing)
        return probs[0][1].item()
        
    def generate_shap_explanation(self, text: str):
        """Generates SHAP values for the email text to explain which words triggered the alert."""
        # SHAP requires a prediction function that takes a list of strings and returns a numpy array of probabilities
        def predict_fn(texts):
            text_list = [str(t) for t in texts]
            inputs = self.tokenizer(text_list, return_tensors="pt", truncation=True, max_length=512, padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            return probs.cpu().numpy()
            
        explainer = shap.Explainer(predict_fn, self.tokenizer)
        shap_values = explainer([text])
        
        # Extract the words and their impact scores for the "Phishing" class
        # (Assuming binary classification where we want the impact on class 1)
        word_impacts = []
        if len(shap_values.values) > 0 and len(shap_values.data) > 0:
            # Get values for the first (and only) text in the batch, for class 1
            values = shap_values.values[0][:, 1] if len(shap_values.values[0].shape) > 1 else shap_values.values[0]
            words = shap_values.data[0]
            
            for word, impact in zip(words, values):
                if word.strip():
                    word_impacts.append({
                        "word": word,
                        "impact": float(impact)
                    })
                    
        # Sort by absolute impact to find the most influential words
        word_impacts.sort(key=lambda x: abs(x["impact"]), reverse=True)
        return word_impacts[:10] # Return top 10 most influential words
