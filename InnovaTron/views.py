import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from rest_framework import status
from transformers import MarianMTModel, MarianTokenizer
from openvino.runtime import Core
from google.cloud import speech_v1p1beta1 as speech
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# AI Model setup (Intel OpenVINO)
MODEL_PATH = os.getenv("MODEL_PATH", "path_to_model.xml")  # Replace with your model's path
ie = Core()
compiled_model = None

try:
    model = ie.read_model(model=MODEL_PATH)
    compiled_model = ie.compile_model(model=model, device_name="CPU")
except Exception as e:
    print(f"Error loading AI model: {str(e)}")

def process_ai_data(input_data):
    """AI processing using OpenVINO."""
    if not compiled_model:
        raise ValueError("AI model not loaded.")
    input_tensor = compiled_model.input(0)
    output_tensor = compiled_model.output(0)
    result = compiled_model({input_tensor: input_data})[output_tensor]
    return result.tolist()

# Translation setup (Hugging Face MarianMT)
tokenizer = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-hi")
translation_model = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-en-hi")

def translate_text(text, source_lang="en", target_lang="hi"):
    """Translate text using Hugging Face MarianMT."""
    if target_lang != "hi":
        raise ValueError("This translation model only supports English to Hindi.")
    tokenizer.src_lang = source_lang
    translated = translation_model.generate(**tokenizer(text, return_tensors="pt", padding=True))
    return tokenizer.batch_decode(translated, skip_special_tokens=True)

# Speech-to-Text setup (Google Cloud)
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "path_to_google_credentials.json")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CREDENTIALS_PATH

def speech_to_text(audio_file_path):
    """Convert speech to text using Google Speech API."""
    client = speech.SpeechClient()
    with open(audio_file_path, "rb") as audio_file:
        content = audio_file.read()
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )
    response = client.recognize(config=config, audio=audio)
    return response.results[0].alternatives[0].transcript if response.results else ""

# User Authentication
class SignupView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({"message": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.create_user(username=username, password=password)
            return Response({"message": "Signup successful"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"message": f"Error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({"message": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                refresh = RefreshToken.for_user(user)
                return Response({
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh)
                })
            return Response({"message": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"message": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)

# AI Processing API
class AIProcessingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        input_data = request.data.get('input_data')
        if not input_data:
            return Response({"message": "No input data provided"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = process_ai_data(input_data)
            return Response({"message": "Processing successful", "result": result})
        except Exception as e:
            return Response({"message": f"Error during processing: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Speech-to-Text API
class SpeechToTextView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file = request.FILES.get('audio_file')
        if not file:
            return Response({"message": "No audio file provided"}, status=status.HTTP_400_BAD_REQUEST)
        file_path = f"./uploads/{file.name}"
        os.makedirs("./uploads", exist_ok=True)  # Ensure the directory exists
        with open(file_path, "wb") as f:
            f.write(file.read())
        try:
            transcript = speech_to_text(file_path)
            os.remove(file_path)  # Clean up uploaded file
            return Response({"message": "Speech-to-text successful", "transcript": transcript})
        except Exception as e:
            return Response({"message": f"Error during speech-to-text: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Translation API
class TranslateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        text = request.data.get('text')
        source_lang = request.data.get('source_lang', 'en')
        target_lang = request.data.get('target_lang', 'hi')  # Default to Hindi

        if not text:
            return Response({"message": "No text provided"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            translation = translate_text(text, source_lang, target_lang)
            return Response({"message": "Translation successful", "translation": translation})
        except Exception as e:
            return Response({"message": f"Error during translation: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
