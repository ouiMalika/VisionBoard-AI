from celery import Celery
import torch, requests, io
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans
from transformers import CLIPProcessor, CLIPModel

app = Celery("worker", broker="redis://redis:6379/0")
device = "cuda" if torch.cuda.is_available() else "cpu"

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

@app.task(name="tasks.cluster_images")
def cluster_images(image_urls, n_clusters=5):
    embeddings = []
    for url in image_urls:
        try:
            img = Image.open(io.BytesIO(requests.get(url, timeout=10).content)).convert("RGB")
            inputs = processor(images=img, return_tensors="pt").to(device)
            with torch.no_grad():
                emb = model.get_image_features(**inputs)
            embeddings.append(emb.cpu().numpy())
        except Exception as e:
            print(f"Skipping invalid URL: {url} ({e})")

    if not embeddings:
        return {"error": "no valid images"}
    
    X = np.vstack(embeddings)
    labels = KMeans(n_clusters=n_clusters, random_state=42).fit_predict(X)
    clusters = {int(k): [] for k in range(n_clusters)}
    for i, label in enumerate(labels):
        clusters[int(label)].append(image_urls[i])
    return clusters