import json
import logging
from django.contrib.auth.models import User
from django.contrib.auth import logout, login, authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import CarMake, CarModel
from .populate import initiate
from .restapis import get_request, analyze_review_sentiments

# Get an instance of a logger
logger = logging.getLogger(__name__)


@csrf_exempt
def login_user(request):
    """Authenticate user and log them in."""
    data = json.loads(request.body)
    username = data.get('userName')
    password = data.get('password')

    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)
        return JsonResponse({
            "userName": username, "status": "Authenticated"
        })
    else:
        return JsonResponse({
            "userName": username, "status": "Unauthenticated"
        })


def logout_request(request):
    """Log the user out."""
    logout(request)
    return JsonResponse({"userName": ""})


@csrf_exempt
def registration(request):
    """Register a new user."""
    try:
        data = json.loads(request.body)
        username = data.get('userName')
        password = data.get('password')
        first_name = data.get('firstName')
        last_name = data.get('lastName')
        email = data.get('email')

        if User.objects.filter(username=username).exists():
            return JsonResponse({
                "userName": username, "error": "Already Registered"
            }, status=400)

        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            email=email
        )
        login(request, user)
        return JsonResponse({
            "userName": username, "status": "Authenticated"
        })
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {e}")
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return JsonResponse({"error": "An error occurred"}, status=500)


def get_cars(request):
    """Get a list of cars."""
    if CarMake.objects.count() == 0:
        initiate()

    car_models = CarModel.objects.select_related('car_make')
    cars = [{
        "CarModel": car_model.name,
        "CarMake": car_model.car_make.name}
        for car_model in car_models]

    return JsonResponse({"CarModels": cars})


@csrf_exempt
def submit_review(request):
    """Submit a review for a car."""
    try:
        data = json.loads(request.body)
        review_text = data.get('reviewText')
        car_model_id = data.get('carModelId')

        if not review_text or not car_model_id:
            return JsonResponse({
                "error": "Review text and car model ID are required"
            }, status=400)

        # Analyze the sentiment of the review
        sentiment = analyze_review_sentiments(review_text)

        return JsonResponse({
            "status": "Review submitted", "sentiment": sentiment
        })
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {e}")
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return JsonResponse({"error": "An error occurred"}, status=500)


@csrf_exempt
def get_reviews(request):
    """Get reviews for a specific car model."""
    try:
        data = json.loads(request.body)
        car_model_id = data.get('carModelId')

        if not car_model_id:
            return JsonResponse({
                "error": "Car model ID is required"
            }, status=400)

        # Update with your actual API endpoint
        reviews = get_request(f'/reviews/{car_model_id}')
        return JsonResponse({"reviews": reviews})
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {e}")
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return JsonResponse({"error": "An error occurred"}, status=500)
