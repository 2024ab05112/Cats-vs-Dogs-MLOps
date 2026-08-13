"""Views for Cats vs Dogs prediction web app."""
import os

import requests
from django.conf import settings
from django.shortcuts import render


def index(request):
    """Render the main upload page."""
    return render(request, "index.html")


def predict(request):
    """
    Handle image upload, forward to backend API, and show result.
    """
    if request.method != "POST" or "image" not in request.FILES:
        return render(request, "index.html", {"error": "Please upload an image."})

    image_file = request.FILES["image"]
    backend_url = f"{settings.BACKEND_API_URL}/api/predict"

    try:
        response = requests.post(
            backend_url,
            files={"file": (image_file.name, image_file.read(), image_file.content_type)},
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.ConnectionError:
        return render(request, "index.html", {"error": "Cannot connect to inference backend."})
    except Exception as exc:
        return render(request, "index.html", {"error": str(exc)})

    return render(request, "result.html", {"result": result, "filename": image_file.name})
