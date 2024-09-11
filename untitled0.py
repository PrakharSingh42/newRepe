# -*- coding: utf-8 -*-
"""Untitled0.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1egVAJTjSo2m-KaPkka9Vm0EYEk_G62S6
"""

import os
import json
import requests
import torch
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from PIL import Image
import torchvision.models as models
from transformers import BertTokenizer, BertModel, BertConfig
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import random

# COCO Dataset paths
images_path = "/path/to/coco/images/train2017"
annotations_path = "/path/to/coco/annotations/captions_train2017.json"

# Load COCO annotations
with open(annotations_path, 'r') as f:
    coco_annotations = json.load(f)

# Process annotations
annotations = coco_annotations['annotations']
images = coco_annotations['images']

# Data augmentation and normalization for image processing
transform = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Custom dataset for COCO images and captions
class COCOCaptionDataset(Dataset):
    def __init__(self, annotations, images, transform):
        self.annotations = annotations
        self.images = images
        self.transform = transform

    def __len__(self):
        return len(self.annotations)

    def __getitem__(self, idx):
        annotation = self.annotations[idx]
        image_id = annotation['image_id']
        caption = annotation['caption']

        image_file = [img for img in self.images if img['id'] == image_id][0]['file_name']
        image = Image.open(os.path.join(images_path, image_file)).convert('RGB')

        if self.transform:
            image = self.transform(image)

        return image, caption

# Create dataset and data loader
dataset = COCOCaptionDataset(annotations, images, transform)
data_loader = DataLoader(dataset, batch_size=32, shuffle=True)

!pip install tensorflow torch torchvision transformers requests kaggle

# Load Pretrained ResNet for feature extraction
resnet = models.resnet50(pretrained=True)
modules = list(resnet.children())[:-2]  # Remove fully connected layers
resnet = torch.nn.Sequential(*modules)

# Freeze ResNet parameters
for param in resnet.parameters():
    param.requires_grad = False

# GPT-2 Model for Caption Generation
gpt2_tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
gpt2_model = GPT2LMHeadModel.from_pretrained("gpt2")
gpt2_model.resize_token_embeddings(len(gpt2_tokenizer))

# Function to generate caption using GPT-2
def generate_caption(image_features):
    input_ids = gpt2_tokenizer("<|startoftext|>", return_tensors="pt").input_ids

    # Pass image features as initial embeddings for GPT-2
    gpt2_output = gpt2_model.generate(
        input_ids=input_ids,
        max_length=50,
        num_return_sequences=1,
        pad_token_id=gpt2_tokenizer.eos_token_id
    )

    caption = gpt2_tokenizer.decode(gpt2_output[0], skip_special_tokens=True)
    return caption

# Fetching weather and location data using an API
def get_weather_and_location(lat, lon):
    weather_api_key = "YOUR_API_KEY"
    weather_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={weather_api_key}"
    response = requests.get(weather_url)
    data = response.json()

    location = data['name']
    weather = data['weather'][0]['description']
    time_of_day = "day" if data['dt'] < data['sys']['sunset'] else "night"

    return weather, location, time_of_day

# Example lat, lon for New York City
lat, lon = 40.7128, -74.0060
weather, location, time_of_day = get_weather_and_location(lat, lon)

print(f"Weather: {weather}, Location: {location}, Time of Day: {time_of_day}")

def generate_dynamic_caption(image, lat, lon):
    # Get image features from ResNet
    image_features = resnet(image.unsqueeze(0))

    # Get contextual data
    weather, location, time_of_day = get_weather_and_location(lat, lon)

    # Generate base caption from GPT-2
    base_caption = generate_caption(image_features)

    # Add context to the caption
    dynamic_caption = f"{base_caption}. The image was taken in {location} during a {weather} {time_of_day}."

    return dynamic_caption

# Test the caption generation
for images, captions in data_loader:
    image = images[0]
    lat, lon = 40.7128, -74.0060  # Example lat, lon for NYC
    caption = generate_dynamic_caption(image, lat, lon)
    print(caption)
    break