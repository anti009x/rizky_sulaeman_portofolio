import ollama
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import os
import time
from time import sleep
from litellm import completion
import requests
from bs4 import BeautifulSoup
import urllib3


# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@csrf_exempt
@require_http_methods(["POST"])
def process_message(request):
    try:
        # Check if the request is multipart (FormData submission)
        if request.content_type.startswith('multipart/form-data'):
            prompt = request.POST.get('message')
            model_choice = request.POST.get('model', 'calista:latest')
        else:
            data = json.loads(request.body)
            prompt = data.get('message')
            model_choice = data.get('model', 'calista:latest')
        
        if not prompt:
            return JsonResponse({'error': 'No message provided'}, status=400)

        response_stream = ollama.generate(
            model=model_choice.lower(),
            prompt=prompt,
            stream=True
        )

        def stream_response():
            for chunk in response_stream:
                text = chunk.get('response', '')
                yield text

        return StreamingHttpResponse(stream_response(), content_type='text/plain')
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def prompt_model(prompt, model="calista:latest"):
    response = ""
    response_stream = ollama.generate(
        model=model,
        prompt=prompt,
        stream=True
    )

    for chunk in response_stream:
        response += chunk.get('response', '')
    return response




  