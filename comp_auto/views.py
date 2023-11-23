from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count
from .forms import RegistrationForm, UserResponseForm,UploadFileForm,AnotherUserResponseForm
from .models import UserResponse, Report,UploadedFile,AddMoreResponse
from django.contrib.auth.decorators import login_required
import xhtml2pdf.pisa as pisa
from django.views.generic import View
from django.template.loader import get_template
from io import BytesIO
from django.core.files import File
from django.http import JsonResponse
from django.forms import formset_factory
from django.views.decorators.http import require_GET
import matplotlib.pyplot as plt
import os
import base64
import matplotlib
matplotlib.use('Agg')
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
    circulars_instance=UploadedFile.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request,'genreport.html',{'circulars_instance':circulars_instance})

@login_required(login_url='login')
def file_upload(request):
    if request.method=='POST':
        form=UploadFileForm(request.POST,request.FILES)
        print(form.errors)
        if 'AddButton' in request.POST:
           if form.is_valid():
              uploaded_file = form.save(commit=False)
              uploaded_file.user = request.user
              uploaded_file.save()
              messages.success(request, 'File uploaded successfully.')
              return redirect('upload_circulars')
           else:
              return HttpResponse("Invalid Form") 
        elif 'SubmitButton' in request.POST:
            if form.is_valid():
              uploaded_file = form.save(commit=False)
              uploaded_file.user = request.user
              uploaded_file.save()
              messages.success(request, 'File uploaded successfully.')
              return redirect('genreport')
            else:
              return HttpResponse("Invalid Form")   
        
    else:
        form = UploadFileForm()
    return render(request,'genreport.html',{'form':form})   


@login_required(login_url='login')
def responses(request):
    if request.method=='POST':
       form=UserResponseForm(request.POST)
       if 'nextButton' in request.POST:
            if form.is_valid():
                form.instance.user=request.user
                form.save()
                messages.success(request, 'Your response has been saved.')
                return redirect('responses')
            else:
                return HttpResponse("Invalid Form")
       elif 'skipButton' in request.POST:
            return redirect('responses')
       elif 'addmoreButton' in request.POST:
            if form.is_valid():
                form.instance.user=request.user
                form.save()
                messages.success(request, 'Your response has been saved.')
                return redirect('add_moreques')
            else:
                return HttpResponse("Invalid Form")
       elif 'submitButton' in request.POST:
            if form.is_valid():
                form.instance.user=request.user
                form.save()
                messages.success(request, 'Your response has been saved.')
                return redirect('show_report')
            else:
                return HttpResponse("Invalid Form")
    else:
        form=UserResponseForm()
        return render(request,'audit_questionare.html',{'form':form})   

def add_more(request):
    if request.method=='POST':
       form=AnotherUserResponseForm(request.POST)
       if 'addmoreButton' in request.POST:
           if form.is_valid():
              form.instance.user=request.user
              form.save()
              messages.success(request, 'Your response has been saved.')
              return redirect('add_moreques')
           else:
              print(form.errors) 
              return HttpResponse("Invalid Form")
       elif 'submitButton' in request.POST:
            if form.is_valid():
                form.instance.user=request.user
                form.save()
                messages.success(request, 'Your response has been saved.')
                return redirect('show_report')
            else:
                return HttpResponse("Invalid Form")    
    else:
        form=AnotherUserResponseForm()
    return render(request,'Add_more.html',{'form':form})    


@login_required(login_url='login')
def show_report(request):
    user_responses = UserResponse.objects.filter(user=request.user)
    add_more_responses=AddMoreResponse.objects.filter(user=request.user)
    context={
     'user_responses':user_responses,
     'add_more_responses':add_more_responses
    }
    return render(request,'results.html', context)

@login_required(login_url='login')
def myreport(request):
    user_reports=Report.objects.filter(user=request.user).order_by('-created_at')
    return render(request,'myreport.html',{'user_reports':user_reports})

@login_required(login_url='login')
def PDFView(request):
    Uploaded_File=UploadedFile.objects.filter(user=request.user)
    user_responses = UserResponse.objects.filter(user=request.user)
    add_more_responses=AddMoreResponse.objects.filter(user=request.user)
    template = get_template('results.html')
    context = {'user_responses': user_responses,'add_more_responses':add_more_responses}
    html = template.render(context)

    pdf_buffer = BytesIO()

    status = pisa.CreatePDF(html, pdf_buffer)

    if status.err:
        return HttpResponse('Error during PDF generation.')

    # Save the generated PDF content to the Reports model
    report = Report.objects.create(user=request.user)

    # Move the buffer's cursor to the beginning before saving
    pdf_buffer.seek(0)

    # Save the content to the pdf_file field using a Django File object
    report.pdf_file.save('data_report.pdf', File(pdf_buffer), save=True)

    pdf_buffer.close()

    # Deleting User Responses
    Uploaded_File.delete()
    user_responses.delete()
    add_more_responses.delete()

    return redirect('myreport')

@login_required(login_url='login')
def delete_report(request,report_id):
    if request.method == 'POST':
        report=get_object_or_404(Report,id=report_id)
        report.delete()
        return redirect('myreport')
    else:    
        return JsonResponse({'message': 'Invalid Request'})
    

@login_required
def pie_chart(request):
    plt.switch_backend('Agg')
    # Get counts for compliance types
    user_responses_counts = UserResponse.objects.values('compliance_type').annotate(count=Count('compliance_type'))
    add_more_responses_counts = AddMoreResponse.objects.values('compliance_type').annotate(count=Count('compliance_type'))

    combined_counts = user_responses_counts.union(add_more_responses_counts)

    compliant_count = 0
    partially_compliant_count = 0
    non_compliant_count = 0

    for entry in combined_counts:
        if entry['compliance_type'] == 'compliant':
            compliant_count += entry['count']
        elif entry['compliance_type'] == 'partially-compliant':
            partially_compliant_count += entry['count']
        elif entry['compliance_type'] == 'non-compliant':
            non_compliant_count += entry['count']

    # data = [compliant_count, partially_compliant_count, non_compliant_count]
    # labels = ["Compliant", "Partially Compliant", "Non-Compliant"]

    # Create pie chart
    # plt.pie(data, labels=labels, colors=['green', '#FFC200', 'red'])

    # chart_dir=os.path.join('static', 'charts')
    # os.makedirs(chart_dir,exist_ok=True)
    # chart_path = os.path.join(chart_dir, 'compliance_chart.png')
    # print(f"Chart Path: {chart_path}")
    # plt.savefig(chart_path, format='png')
    # plt.close()

    # Prepare chart data for rendering in the template
    # chart_data = base64.b64encode(open(chart_path, 'rb').read()).decode('utf-8')

    # Pass data to the template
    context = {
        'compliant_count': compliant_count,
        'partially_compliant_count': partially_compliant_count,
        'non_compliant_count': non_compliant_count,
    }

    return render(request, 'results.html', context)

@login_required(login_url='login')
def save_pdf(request):
    if request.method=='POST' and request.FILES.get('pdf_file'):
       user=request.user
       pdf_file=request.FILES('pdf_file')
       report=Report.objects.create(user=user)
       report.pdf_file.save(pdf_file.name, pdf_file)
       return JsonResponse({'message': 'PDF saved successfully.'})
    return JsonResponse({'message': 'Error saving PDF.'}, status=400)

def upload_circulars(request):
    return render(request,'upload_circulars.html')

def audit_questions(request):
    return render(request,'audit_questionare.html')

def add_moreques(request):
    return render(request,'Add_more.html')

@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('form')
