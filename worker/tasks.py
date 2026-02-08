from celery import Celery
import torch
import requests
import io
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans
from transformers import CLIPProcessor, CLIPModel

app = Celery("worker", broker="redis://redis:6379/0")
device = "cuda" if torch.cuda.is_available() else "cpu"

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# Aesthetic vocabulary for zero-shot tagging
AESTHETIC_LABELS = [
    "minimalist", "vintage", "retro", "modern", "rustic",
    "bohemian", "industrial", "cozy", "elegant", "bold",
    "pastel", "monochrome", "colorful", "dark and moody", "bright and airy",
    "warm tones", "cool tones", "earthy", "nature", "urban",
    "abstract", "geometric", "organic", "romantic", "edgy",
    "tropical", "scandinavian", "art deco", "cottage core", "futuristic",
    "food and drink", "fashion", "architecture", "travel", "portrait",
    "flat lay", "landscape", "texture", "pattern", "typography",
]


def _get_image_embedding(url):
    """Download an image and return its CLIP embedding."""
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    img = Image.open(io.BytesIO(resp.content)).convert("RGB")
    inputs = processor(images=img, return_tensors="pt").to(device)
    with torch.no_grad():
        emb = model.get_image_features(**inputs)
    return emb.cpu().numpy()


def _tag_cluster(image_urls, top_k=4):
    """Use CLIP zero-shot to find the best aesthetic tags for a group of images.

    Loads a sample of images from the cluster, scores them against
    AESTHETIC_LABELS, and returns the top_k labels.
    """
    # Sample up to 6 images to keep tagging fast
    sample = image_urls[:6]
    images = []
    for url in sample:
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            images.append(
                Image.open(io.BytesIO(resp.content)).convert("RGB")
            )
        except Exception:
            continue

    if not images:
        return []

    text_inputs = processor(
        text=[f"a photo that is {label}" for label in AESTHETIC_LABELS],
        return_tensors="pt",
        padding=True,
    ).to(device)
    image_inputs = processor(images=images, return_tensors="pt").to(device)

    with torch.no_grad():
        image_features = model.get_image_features(**image_inputs)
        text_features = model.get_text_features(**text_inputs)

    # Normalise and compute similarities
    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
    text_features = text_features / text_features.norm(dim=-1, keepdim=True)

    # Average similarity across all images in the cluster
    similarities = (image_features @ text_features.T).mean(dim=0)
    top_indices = similarities.topk(top_k).indices.tolist()
    return [AESTHETIC_LABELS[i] for i in top_indices]


@app.task(name="tasks.cluster_images")
def cluster_images(image_urls, n_clusters=5):
    """Cluster images by visual similarity and tag each cluster with aesthetics."""
    embeddings = []
    valid_urls = []

    for url in image_urls:
        try:
            emb = _get_image_embedding(url)
            embeddings.append(emb)
            valid_urls.append(url)
        except Exception as e:
            print(f"Skipping invalid URL: {url} ({e})")

    if not embeddings:
        return {"error": "no valid images"}

    X = np.vstack(embeddings)

    # Don't request more clusters than we have images
    k = min(n_clusters, len(valid_urls))
    labels = KMeans(n_clusters=k, random_state=42, n_init="auto").fit_predict(X)

    # Group URLs by cluster
    clusters = {int(c): [] for c in range(k)}
    for i, label in enumerate(labels):
        clusters[int(label)].append(valid_urls[i])

    # Tag each cluster with aesthetic keywords
    result = {}
    for cluster_id, urls in clusters.items():
        tags = _tag_cluster(urls)
        result[cluster_id] = {
            "images": urls,
            "tags": tags,
        }

    return result