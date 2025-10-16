from celery import shared_task
from worker.tasks import cluster_images as worker_cluster_images

@shared_task
def cluster_images(image_urls, n_clusters=5):
    return worker_cluster_images(image_urls, n_clusters)
