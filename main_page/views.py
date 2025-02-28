from django.shortcuts import render
import random

# Create your views here.

def index(request):
    return render(request, 'index.html')

def meteor_preview(request):
    # Generate random positions and delays for meteors
    meteor_count = random.randint(10, 20)  # Random number between 10 and 20
    
    context = {
        'meteor_range': range(meteor_count),
    }
    return render(request, 'calista.html', context)