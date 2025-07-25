from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET, require_http_methods
import json
import os

from .models import SharedDocument, SharedImage

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def display_page(request):
    """
    Renders the main application page.
    """
    return render(request, 'share/index.html')

@csrf_exempt
@require_POST
def update_text(request):
    """
    Receives text updates from the client and saves them to the database.
    """
    try:
        data = json.loads(request.body)
        text = data.get('text', '')
        client_public_ip = data.get('public_ip', '')
        client_local_ip = get_client_ip(request)

        if not client_public_ip:
            return JsonResponse({'status': 'error', 'message': 'Public IP not provided.'}, status=400)

        shared_doc, created = SharedDocument.objects.get_or_create(public_ip=client_public_ip)
        shared_doc.content = text
        shared_doc.local_ip = client_local_ip
        shared_doc.save()

        return JsonResponse({'status': 'success'})
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_GET
def get_content(request):
    """
    Fetches the latest text and images for the requesting client's public IP.
    """
    client_public_ip = request.GET.get('public_ip', '')

    if not client_public_ip:
        return JsonResponse({'status': 'error', 'message': 'Public IP not provided.'}, status=400)

    # Get text content
    text_content = ''
    text_local_ip = 'N/A'
    text_last_updated = 'N/A'
    try:
        shared_doc = SharedDocument.objects.get(public_ip=client_public_ip)
        text_content = shared_doc.content
        text_local_ip = shared_doc.local_ip or 'N/A'
        text_last_updated = shared_doc.last_updated.strftime("%Y-%m-%d %H:%M:%S")
    except SharedDocument.DoesNotExist:
        pass

    images_data = []
    images = SharedImage.objects.filter(public_ip=client_public_ip).order_by('-uploaded_at')[:10]
    for img in images:
        images_data.append({
            'id': img.id,
            'url': img.image.url,
            'uploaded_at': img.uploaded_at.strftime("%Y-%m-%d %H:%M:%S"),
            'local_ip': img.local_ip or 'N/A'
        })

    return JsonResponse({
        'text': text_content,
        'images': images_data,
        'text_local_ip': text_local_ip,
        'text_last_updated': text_last_updated
    })

@csrf_exempt
@require_POST
def upload_image(request):
    """
    Handles image uploads.
    """
    if 'image' not in request.FILES:
        return JsonResponse({'status': 'error', 'message': 'No image file uploaded.'}, status=400)

    image_file = request.FILES['image']
    public_ip = request.POST.get('public_ip')
    local_ip = get_client_ip(request)

    if not public_ip:
        return JsonResponse({'status': 'error', 'message': 'Public IP not provided.'}, status=400)

    try:
        shared_image = SharedImage(image=image_file, public_ip=public_ip, local_ip=local_ip)
        shared_image.save()
        return JsonResponse({
            'status': 'success',
            'image_url': shared_image.image.url,
            'uploaded_at': shared_image.uploaded_at.strftime("%Y-%m-%d %H:%M:%S"),
            'local_ip': shared_image.local_ip or 'N/A'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@csrf_exempt # Use proper CSRF handling in production (e.g., Delete method)
@require_http_methods(["DELETE", "POST"]) # Allow POST for AJAX if DELETE isn't easily supported
def delete_image(request, image_id):
    """
    Deletes a specific image by its ID.
    """
    try:
        image = SharedImage.objects.get(id=image_id)
        # Optional: Verify public_ip matches requesting user's public IP
        # if request.POST.get('public_ip') != str(image.public_ip):
        #     return JsonResponse({'status': 'error', 'message': 'Unauthorized deletion.'}, status=403)

        # Delete the actual file from storage
        if os.path.exists(image.image.path):
            os.remove(image.image.path)
        
        image.delete() # Delete from database
        return JsonResponse({'status': 'success', 'message': 'Image deleted.'})
    except SharedImage.DoesNotExist:
        raise Http404("Image not found.")
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt # Use proper CSRF handling in production
@require_POST
def clear_all_images(request):
    """
    Deletes all images associated with a specific public IP.
    """
    try:
        data = json.loads(request.body)
        client_public_ip = data.get('public_ip', '')

        if not client_public_ip:
            return JsonResponse({'status': 'error', 'message': 'Public IP not provided.'}, status=400)

        images_to_delete = SharedImage.objects.filter(public_ip=client_public_ip)
        count = images_to_delete.count()

        # Delete files from storage first
        for image in images_to_delete:
            if os.path.exists(image.image.path):
                os.remove(image.image.path)
        
        images_to_delete.delete() # Delete from database

        return JsonResponse({'status': 'success', 'message': f'{count} images cleared for {client_public_ip}.'})
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)