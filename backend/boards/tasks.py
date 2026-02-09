from celery import shared_task

@shared_task(name="tasks.cluster_images")
def cluster_images(image_urls, n_clusters):
    # TODO: your clustering logic here
    return {
        "0": {
            "images": image_urls,
            "tags": ["example"]
        }
    }
