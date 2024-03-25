from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count
from .forms import RegistrationForm, UserResponseForm,UploadFileForm,AnotherUserResponseForm,RenameReportForm
from .models import UserResponse, Report,UploadedFile,AddMoreResponse,Audit_point_summaries,Audit_point_summaries
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from django.template.loader import get_template
from io import BytesIO
from django.core.files import File
from django.http import JsonResponse
from django.forms import formset_factory
from django.views.decorators.http import require_GET
import matplotlib.pyplot as plt,os,io,base64,xhtml2pdf.pisa as pisa
from PIL import Image
from pdf2image import convert_from_path
from transformers import pipeline, BartForConditionalGeneration, BartTokenizer
import pytesseract,fitz
from urllib3 import PoolManager
import matplotlib
from django.urls import reverse
import matplotlib.pyplot as plt
matplotlib.use('Agg')
import pickle,ssl
from nltk.tokenize import sent_tokenize
from nltk.probability import FreqDist
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import re ,subprocess,sys
from .circulars_processing import (
    convert_pdf_to_images,
    extracted_text_from_img,
    split_passages,
)
    
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
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
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
                
                # text extraction
                circulars_instance = UploadedFile.objects.filter(user=request.user).last()
                pdf_path = circulars_instance.file.path
                images = convert_pdf_to_images(pdf_path)

                extracted_text = ''
                for i, image in enumerate(images):
                    image_path = f"temp_image_{i}.png"
                    image.save(image_path, "PNG")
                    text = extracted_text_from_img(image_path)
                    extracted_text += f"Page {i + 1}:\n{text}\n{'-' * 40}\n"
                
                # print("Extracted Text:", extracted_text)

                audit_points = split_passages(extracted_text)
                for i,point in enumerate(audit_points,start=1):
                    print(f"Point {i}: {point}")

                for i, point in enumerate(audit_points, start=1):
                    summary = generate_summary(point) 
                    Audit_point_summaries.objects.create(user=request.user, audit_point_text=point, summary=summary)   
                # model_path = 'D:\\Vedu study\\TY\\Complaince project\\complaince_proj\\complaince\\model.pkl'
                # model, tokenizer = load_model_and_tokenizer(model_path)
                # summaries = []
                # for i, point in enumerate(audit_points):
                #     summary = summarize(point, model, tokenizer)
                #     summaries.append(summary)
                #     setattr(circulars_instance, f'summary_{i + 1}', summary)

                circulars_instance.save()

                return redirect('genreport')
            else:
                return HttpResponse("Invalid Form")

    else:
        form = UploadFileForm()

    return render(request, 'genreport.html', {'form': form}) 

def convert_pdf_to_images(pdf_path):
    try:
        doc=fitz.open(pdf_path)
        images=[]
        for page_num in range(doc.page_count):
            page=doc[page_num]
            image=page.get_pixmap()
            img = Image.frombytes("RGB", (image.width, image.height), image.samples)
            images.append(img)
        return images
    except Exception as e:
        print(f"Error converting PDF to images: {e}")
        return []
    finally:
        if doc:
            doc.close()

def extracted_text_from_img(image_path):
    img=None
    try:
       img=Image.open(image_path)
       text=pytesseract.image_to_string(img)
       return text
    except Exception as e:
       print(f"Error extracting text from image: {e}")
       return ""
    finally:
        if img:
            img.close()

def split_passages(text):
    point_pattern = re.compile(r'\b\d+\.\d*\s+|[IVXLCDMivxlcdm]+\.\d*\s+')

    audit_points = []
    last_index = 0

    for match in point_pattern.finditer(text):
        index = match.start()
        audit_points.append(text[last_index:index].strip())
        last_index = match.end()

    audit_points.append(text[last_index:].strip())

    return audit_points

# def summarize(text, model, tokenizer):
#     summarizer = pipeline("summarization", model=model, tokenizer=tokenizer)
#     summary = summarizer(text, max_length=150, min_length=50, length_penalty=2.0, num_beams=4, early_stopping=True)[0]['summary_text']
#     return summary


def load_model_and_tokenizer(file_path):
    with open(file_path, 'rb') as model_file:
         model, tokenizer = pickle.load(model_file)
    return model, tokenizer

def generate_summary(text, num_sentences=2):
    # Tokenize text into sentences
    sentences = sent_tokenize(text)
    # Tokenize text into words
    words = word_tokenize(text)
    # Remove stopwords
    stop_words = set(stopwords.words("english"))
    filtered_words = [word for word in words if word.lower() not in stop_words]
    # Compute TF-IDF scores
    tfidf = TfidfVectorizer()
    tfidf_matrix = tfidf.fit_transform(sentences)
    tfidf_matrix = tfidf_matrix.toarray()

    # Calculate sentence scores based on TF-IDF
    sentence_scores = np.sum(tfidf_matrix, axis=1)

    # Select top sentences based on scores
    top_sentences_indices = sentence_scores.argsort()[-num_sentences:][::-1]
    top_sentences = [sentences[index] for index in top_sentences_indices]

    # Combine selected sentences to form the summary
    summary = ' '.join(top_sentences)

    return summary


@login_required(login_url='login')
def responses(request):
    audit_points_summaries = Audit_point_summaries.objects.all()
    if request.method == 'POST':
        form = UserResponseForm(request.POST)
        messages.success(request, 'Your response has been saved.')
        if 'nextButton' in request.POST:
            if form.is_valid():
                form.instance.user = request.user
                form.save()
                return redirect('responses')
        elif 'skipButton' in request.POST:
            return redirect('responses')
        elif 'addmoreButton' in request.POST:
            if form.is_valid():
                form.instance.user = request.user
                form.save()
                messages.success(request, 'Your response has been saved.')
                return redirect('add_moreques')
            else:
                print(form.errors) 
                return HttpResponse("Invalid Form")
        elif 'submitButton' in request.POST:
            if form.is_valid():
                form.instance.user = request.user
                form.save()
                messages.success(request, 'Your response has been saved.')
                return redirect('show_report')
            else:
                print(form.errors) 
                return HttpResponse("Invalid Form")
    else:
        form = UserResponseForm()

    return render(request, 'audit_questionare.html', {'form': form, 'audit_points_summaries': audit_points_summaries})

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
    chart_data=pie_chart(user=request.user)
    context={
    'user_responses':user_responses,
    #  'add_more_responses':add_more_responses,
     'chart_data': chart_data
    }
    
    return render(request, 'thank_you.html', context)
    

@login_required(login_url='login')
def myreport(request):
    user_reports=Report.objects.filter(user=request.user).order_by('-created_at')
    return render(request,'myreport.html',{'user_reports':user_reports})

@login_required(login_url='login')
def PDFView(request):
    Uploaded_File=UploadedFile.objects.filter(user=request.user)
    user_responses = UserResponse.objects.filter(user=request.user)
    add_more_responses=AddMoreResponse.objects.filter(user=request.user)
    audit_point_summaries=Audit_point_summaries.objects.filter(user=request.user)
    chart_data=pie_chart(user=request)
    template = get_template('thank_you.html')
    context = {'user_responses': user_responses,'add_more_responses':add_more_responses,'chart_data':chart_data}
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
    audit_point_summaries.delete()
    return redirect('myreport')

@login_required(login_url='login')
def delete_report(request,report_id):
    if request.method == 'POST':
        report=get_object_or_404(Report,id=report_id)
        report.delete()
        return redirect('myreport')
    else:    
        return JsonResponse({'message': 'Invalid Request'})

@login_required(login_url='login')
def rename_report(request,report_id):
    report=Report.objects.get(pk=report_id)
    if request.method == 'POST':
        form = RenameReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, 'Report renamed successfully.')
            return redirect('myreport')
    else:
        form = RenameReportForm(instance=report)
    return render(request, 'myreport.html', {'form': form, 'report': report})
    
def pie_chart(user):
    # Get counts for compliance types
    plt.switch_backend('Agg')
    user_responses_counts = UserResponse.objects.values('compliance_type').annotate(count=Count('compliance_type'))
    add_more_responses_counts = AddMoreResponse.objects.values('compliance_type').annotate(count=Count('compliance_type'))

    combined_counts = user_responses_counts.union(add_more_responses_counts)

    compliant_count = 0
    partially_compliant_count = 0
    non_compliant_count = 0
    not_applicable_count= 0
    
    for entry in combined_counts:
        if entry['compliance_type'] == 'compliant':
            compliant_count += entry['count']
        elif entry['compliance_type'] == 'partially-compliant':
            partially_compliant_count += entry['count']
        elif entry['compliance_type'] == 'non-compliant':
            non_compliant_count += entry['count']
        elif entry['compliance_type'] == 'not-applicable':
            not_applicable_count += entry['count']
    total_count = compliant_count + partially_compliant_count + non_compliant_count+not_applicable_count

    # Calculate percentages
    compliant_percentage = (compliant_count / total_count) * 100
    partially_compliant_percentage = (partially_compliant_count / total_count) * 100
    non_compliant_percentage = (non_compliant_count / total_count) * 100
    not_applicable_percentage = (not_applicable_count / total_count) * 100

    if total_count == 0:
        print("No data available for pie chart.")
        return None
    data = [compliant_count, partially_compliant_count, non_compliant_count,not_applicable_count]
    labels = [f"Compliant ({compliant_percentage:.2f}%)", f"Partially Compliant ({partially_compliant_percentage:.2f}%)", f"Non-Compliant ({non_compliant_percentage:.2f}%)",f"not-applicable ({not_applicable_percentage:.2f}%)"]

    # Create pie chart
    plt.pie(data, labels=labels, colors=['green', '#FFC200', 'red','#00C8F0'])
    chart_image_buffer=io.BytesIO()
    plt.savefig(chart_image_buffer, format='png')
    plt.close()
    chart_image_buffer.seek(0)

    # Prepare chart data for rendering in the template
    chart_data = base64.b64encode(chart_image_buffer.read()).decode('utf-8')
    return chart_data

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
    audit_points_summaries=Audit_point_summaries.objects.all()
    return render(request,'audit_questionare.html',{'audit_points_summaries': audit_points_summaries})  
    

def add_moreques(request):
    return render(request,'Add_more.html')

def audit_points(request):
    audit_points_summaries = Audit_point_summaries.objects.all()
    total_audit_points = audit_points_summaries.count()
    current_index = int(request.GET.get('current_index', 0))

    if request.method == 'POST':
        form = UserResponseForm(request.POST)
        if form.is_valid():
            user_response = form.save(commit=False)
            user_response.audit_point = audit_points_summaries[current_index]
            user_response.save()
            
            current_index += 1
            if current_index < total_audit_points:
                next_url = reverse('audit_points') + f'?current_index={current_index}'
                return redirect(next_url)
            else:
                return redirect('show_report')
        else:
            # Form is invalid, render the page with the same audit point
            current_audit_point = audit_points_summaries[current_index]
            return render(request, 'audit_response.html', {'current_audit_point': current_audit_point, 'form': form})
    else:
        if current_index < total_audit_points:
            current_audit_point = audit_points_summaries[current_index]
            form = UserResponseForm()
        else:
            return redirect('show_report')  
    
        # Define current_audit_point outside the if-else block to handle the case where request method is GET
        current_audit_point = audit_points_summaries[current_index]

    return render(request, 'audit_response.html', {'current_audit_point': current_audit_point, 'form': form})

# @login_required(login_url='login')
# def thank_you_page(request):
#     user_responses = UserResponse.objects.filter(user=request.user)
#     return render(request, 'thank_you.html', {'user_responses': user_responses})
    
def next_audit_point(request):
    current_index = int(request.POST.get('current_index', 0))
    audit_points_summaries = Audit_point_summaries.objects.all()
    total_points = audit_points_summaries.count()

    # If there are more audit points to display, increment the index
    if current_index < total_points - 1:
        current_index += 1
    else:
        return redirect('summary')  # Redirect to summary page if all points are done

    context = {
        'audit_points_summaries': audit_points_summaries,
        'current_index': current_index,
    }
    return render(request, 'audit_response.html', context)

@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('form')