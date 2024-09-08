import random
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from .models import VerificationCode
from .tasks import send_verification_email
from django.views.decorators.csrf import csrf_protect, csrf_exempt
import json
import os
import time
from openai import AzureOpenAI
from dotenv import load_dotenv
from django.core.files.storage import default_storage
from .document_chatbot import process_document, chat_with_document, GoogleGenerativeAIEmbeddings
from langchain.vectorstores import FAISS
from django.core.mail import send_mail

load_dotenv()

# Azure OpenAI setup
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=api_key,
    api_version="2024-02-15-preview"
)

@csrf_protect
def register(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email already exists'}, status=400)
        
        user = User.objects.create_user(username=username, email=email, password=password)
        code = VerificationCode.generate_code()
        VerificationCode.objects.create(user=user, code=code)
        send_verification_email.delay(email, code)
        
        return JsonResponse({'message': 'Registration successful. Please check your email for verification.'})
    
    return render(request, 'accounts/register.html')

@csrf_protect
def verify_registration(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        code = data.get('code')
        
        try:
            user = User.objects.get(email=email)
            verification = VerificationCode.objects.get(user=user, code=code)
            user.is_active = True
            user.save()
            verification.delete()
            return JsonResponse({'message': 'Account verified successfully'})
        except (User.DoesNotExist, VerificationCode.DoesNotExist):
            return JsonResponse({'error': 'Invalid verification code'}, status=400)
    
@csrf_protect
def login_view(request):
    if request.method == 'GET':
        return render(request, 'accounts/login.html')
    elif request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                if user.is_active:
                    # Generate and save verification code
                    code = str(random.randint(100000, 999999))
                    VerificationCode.objects.create(user=user, code=code)
                    
                    # Send verification code via email
                    send_mail(
                        'Login Verification Code',
                        f'Your verification code is: {code}',
                        'noreply@smartdesk.com',
                        [email],
                        fail_silently=False,
                    )
                    
                    return JsonResponse({'needsVerification': True, 'message': 'Please check your email for the verification code.'})
                else:
                    return JsonResponse({'error': 'Account is not active. Please verify your email.'}, status=400)
            else:
                return JsonResponse({'error': 'Invalid password'}, status=400)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User with this email does not exist'}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)
@csrf_protect
def verify_login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        code = data.get('code')
        
        try:
            user = User.objects.get(email=email)
            verification = VerificationCode.objects.get(user=user, code=code)
            verification.delete()
            login(request, user)
            return JsonResponse({'message': 'Login successful', 'redirect': '/home/'})
        except (User.DoesNotExist, VerificationCode.DoesNotExist):
            return JsonResponse({'error': 'Invalid verification code'}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

def hr_chatbot(user_input):
    hr_context = ("You Are a chat bot for GAIL, which is india's oil firm. "
                  "You should know everything about HR policy and rules, AND IT support, answe the given queries, like an assistant would. Give answers in paragraphs, not points.\n\n, reply with as short answer as possible, but it should make sense, and try to be as specific to GAIL as possible, do not be generic")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            start_time = time.time()
            completion = client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": hr_context},
                    {"role": "user", "content": user_input}
                ],
                max_tokens=800,
                temperature=0.7,
                top_p=0.95,
            )
            end_time = time.time()
            print(f"API call took {end_time - start_time:.2f} seconds")
            return completion.choices[0].message.content
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed. Retrying...")
                time.sleep(1)  # Wait for 1 second before retrying
            else:
                return f"An error occurred: {str(e)}"

@csrf_exempt
def hr_chatbot_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_input = data.get('message', '')
            if not user_input:
                return JsonResponse({'error': 'No message provided'}, status=400)
            response = hr_chatbot(user_input)
            return JsonResponse({'response': response})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def hr_chatbot_page(request):
    return render(request, 'accounts/hr_chatbot.html')

@csrf_exempt
def upload_document(request):
    if request.method == 'POST' and request.FILES.get('document'):
        document = request.FILES['document']
        file_path = default_storage.save(f'documents/{document.name}', document)
        vector_store = process_document(default_storage.path(file_path))
        serialized_vector_store = vector_store.serialize_to_bytes()
        request.session['vector_store'] = serialized_vector_store.decode('latin-1')
        return JsonResponse({'message': 'Document uploaded and processed successfully'})
    return JsonResponse({'error': 'No document provided'}, status=400)

@csrf_exempt
def document_chat(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        question = data.get('message', '')
        serialized_vector_store = request.session.get('vector_store')

        if not serialized_vector_store:
            return JsonResponse({'error': 'No document uploaded'}, status=400)

        vector_store = FAISS.deserialize_from_bytes(
            serialized_vector_store.encode('latin-1'),
            GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=os.getenv("GOOGLE_API_KEY")),
            allow_dangerous_deserialization=True
        )
        response = chat_with_document(vector_store, question)
        return JsonResponse({'response': response})
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def document_chat_page(request):
    return render(request, 'accounts/document_chat.html')

from .chatbot import project_management_chat

@csrf_exempt
def project_management_chatbot_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_input = data.get('message', '')
            if not user_input:
                return JsonResponse({'error': 'No message provided'}, status=400)
            response = project_management_chat(user_input)
            return JsonResponse({'response': response})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def project_management_chatbot_page(request):
    return render(request, 'accounts/project_management_chatbot.html')



from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

@login_required
def get_username(request):
    return JsonResponse({'username': request.user.username})

@login_required
def home(request):
    return render(request, 'accounts/home.html')

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    return render(request, 'accounts/home.html')

def index(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        return redirect('login')


from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect('login')