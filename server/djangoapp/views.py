# Required imports
from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import logout, login, authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging
import json

from .models import CarMake, CarModel
from .populate import initiate
from .restapis import get_request, analyze_review_sentiments, post_review

# Set up logger
logger = logging.getLogger(__name__)


@csrf_exempt
def login_user(request):
    """
    Handle user login. Authenticate user based on the provided credentials in the request.
    
    Args:
        request: HTTP request containing the JSON body with 'userName' and 'password'.
    
    Returns:
        JsonResponse: JSON response with authentication status.
    """
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    user = authenticate(username=username, password=password)
    response_data = {"userName": username}

    if user is not None:
        login(request, user)
        response_data["status"] = "Authenticated"
    return JsonResponse(response_data)


def logout_request(request):
    """
    Handle user logout by logging out the user and resetting the username in the response.
    
    Args:
        request: HTTP request to logout the user.
    
    Returns:
        JsonResponse: JSON response confirming logout.
    """
    logout(request)
    return JsonResponse({"userName": ""})


@csrf_exempt
def registration(request):
    """
    Handle user registration. Create a new user if the username does not exist.
    
    Args:
        request: HTTP request containing the JSON body with user details.
    
    Returns:
        JsonResponse: JSON response indicating success or if the user is already registered.
    """
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    first_name = data['firstName']
    last_name = data['lastName']
    email = data['email']

    try:
        User.objects.get(username=username)
        return JsonResponse({"userName": username, "error": "Already Registered"})
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=username, first_name=first_name, last_name=last_name,
            password=password, email=email
        )
        login(request, user)
        return JsonResponse({"userName": username, "status": "Authenticated"})


def get_cars(request):
    """
    Retrieve all cars, initializing the database if no cars are found.
    
    Args:
        request: HTTP request for retrieving cars.
    
    Returns:
        JsonResponse: JSON response with a list of car models and makes.
    """
    if CarMake.objects.count() == 0:
        initiate()

    car_models = CarModel.objects.select_related('car_make')
    cars = [{"CarModel": car_model.name, "CarMake": car_model.car_make.name}
            for car_model in car_models]
    return JsonResponse({"CarModels": cars})


def get_dealerships(request, state="All"):
    """
    Retrieve a list of dealerships, optionally filtered by state.
    
    Args:
        request: HTTP request for retrieving dealerships.
        state (str): State code for filtering dealerships.
    
    Returns:
        JsonResponse: JSON response with a list of dealerships.
    """
    endpoint = f"/fetchDealers/{state}" if state != "All" else "/fetchDealers"
    dealerships = get_request(endpoint)
    return JsonResponse({"status": 200, "dealers": dealerships})


def get_dealer_reviews(request, dealer_id):
    """
    Retrieve and analyze reviews for a specific dealer.
    
    Args:
        request: HTTP request for retrieving reviews.
        dealer_id (int): Dealer ID for which reviews are fetched.
    
    Returns:
        JsonResponse: JSON response with reviews and their analyzed sentiment.
    """
    if dealer_id:
        endpoint = f"/fetchReviews/dealer/{dealer_id}"
        reviews = get_request(endpoint)

        for review_detail in reviews:
            response = analyze_review_sentiments(review_detail['review'])
            review_detail['sentiment'] = response['sentiment'] if response else "Can't analyze"

        return JsonResponse({"status": 200, "reviews": reviews})
    return JsonResponse({"status": 400, "message": "Bad Request"})


def get_dealer_details(request, dealer_id):
    """
    Retrieve details for a specific dealer.
    
    Args:
        request: HTTP request for retrieving dealer details.
        dealer_id (int): Dealer ID for which details are fetched.
    
    Returns:
        JsonResponse: JSON response with dealer details or error.
    """
    if dealer_id:
        endpoint = f"/fetchDealer/{dealer_id}"
        dealership = get_request(endpoint)
        return JsonResponse({"status": 200, "dealer": dealership})
    return JsonResponse({"status": 400, "message": "Bad Request"})


def add_review(request):
    """
    Add a review for a dealer if the user is authenticated.
    
    Args:
        request: HTTP request containing the JSON body with review details.
    
    Returns:
        JsonResponse: JSON response indicating success or error.
    """
    if not request.user.is_anonymous:
        try:
            data = json.loads(request.body)
            post_review(data)
            return JsonResponse({"status": 200})
        except Exception:
            return JsonResponse({"status": 401, "message": "Error in posting review"})
    return JsonResponse({"status": 403, "message": "Unauthorized"})
