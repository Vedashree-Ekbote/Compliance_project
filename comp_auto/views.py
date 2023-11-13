from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import RegistrationForm
from django.contrib.auth.decorators import login_required

# Create your views here.
def index(request):
    return render(request, 'Home.html')

@login_required(login_url='login')
def dashboard(request):
    auditor_instance = request.user
    return render(request, 'dashboard.html', {'auditor': auditor_instance})

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['registrationUsername']
            email = form.cleaned_data['registrationEmail']
            password = form.cleaned_data['registrationPassword']
            # confpassword=form.cleaned_data['registrationPasswordConfirm']
            # Create the user with the provided information   
        new_user = User.objects.create_user(username=username, email=email, password=password)
        return redirect('form')

    else:
        form = RegistrationForm()

    return render(request, 'Home.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['loginUsername']
        password = request.POST['loginPassword']
        user_auditor = authenticate(request, username=username, password=password)
        if user_auditor is not None:
            login(request, user_auditor)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')
    return redirect('dashboard')

@login_required(login_url='login')
def profile(request):
    auditor_instance = request.user
    return render(request,'profile.html',{'auditor': auditor_instance})

@login_required(login_url='login')
def genreport(request):
    return render(request,'genreport.html')

@login_required(login_url='login')
def myreport(request):
    return render(request,'myreport.html')

@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('form')

def audit_questions(request):
    return render(request,'audit_questionare.html')
