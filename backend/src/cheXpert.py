# prompt: create a class out of the important functions:
import numpy as np
import urllib.request
import skimage
import torch
import torch.nn.functional as F
import torchvision
import torchvision.transforms
import torchxrayvision as xrv

class CheXpert:
    def __init__(self, model_name="densenet121-res224-chex"):
        """
        Initializes the handler with a pre-trained X-ray model.

        Args:
            model_name (str): The name of the torchxrayvision model to load.
                              Defaults to "densenet121-res224-chex".
        """
        self.model = xrv.models.DenseNet(weights=model_name)
        self.model.eval()  # Set model to evaluation mode

    def load_and_preprocess_image(self, image_path):
        """
        Loads an image from a given path, preprocesses it for model input.

        Args:
            image_path (str): The path to the image file.

        Returns:
            torch.Tensor: The processed image tensor ready for inference.
        """
        # Use skimage to read the image
        img = skimage.io.imread(image_path)

        # Normalize image data
        img = xrv.datasets.normalize(img, 255)

        # Check that images are 2D arrays
        if len(img.shape) > 2:
            # If it has more than 2 dimensions, assume it's color and take the first channel
            img = img[:, :, 0]
        if len(img.shape) < 2:
            print(f"Warning: Image at {image_path} has dimension lower than 2.")
            return None

        # Add color channel dimension (expected by torchxrayvision)
        img = img[None, :, :]

        # Apply center crop transform
        transform = torchvision.transforms.Compose([xrv.datasets.XRayCenterCrop()])
        img = transform(img)

        # Convert numpy array to torch tensor and add batch dimension
        img_tensor = torch.from_numpy(img).unsqueeze(0)

        return img_tensor

    def predict(self, img_tensor):
        """
        Performs inference on the preprocessed image tensor.

        Args:
            img_tensor (torch.Tensor): The preprocessed image tensor.

        Returns:
            dict: A dictionary mapping pathology names to prediction scores.
        """
        if img_tensor is None:
            return {}

        with torch.no_grad():
            outputs = self.model(img_tensor).cpu() # Move output to CPU

        # Format the output as a dictionary
        prediction_output = {
            k: float(v)
            for k, v in zip(xrv.datasets.default_pathologies, outputs[0].detach().numpy())
        }
        return prediction_output

    def analyze_image(self, image_path):
        """
        Loads, preprocesses, and analyzes an image, returning the pathology predictions.

        Args:
            image_path (str): The path to the image file.

        Returns:
            dict: A dictionary mapping pathology names to prediction scores.
        """
        img_tensor = self.load_and_preprocess_image(image_path)
        if img_tensor is None:
            return {}
        predictions = self.predict(img_tensor)
        return predictions