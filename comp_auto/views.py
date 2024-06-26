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
# from transformers import pipeline, BartForConditionalGeneration, BartTokenizer
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
# from transformers import T5ForConditionalGeneration, T5Tokenizer
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
import nltk
nltk.download('punkt')
nltk.download('stopwords')
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import re ,subprocess,sys
import spacy

# model = T5ForConditionalGeneration.from_pretrained("t5-small")
# tokenizer = T5Tokenizer.from_pretrained("t5-small")

# tokenizer = AutoTokenizer.from_pretrained("sshleifer/distilbart-xsum-12-6")
# model = AutoModelForSeq2SeqLM.from_pretrained("sshleifer/distilbart-xsum-12-6")

# Create your views here.
def index(request):
    return render(request, 'Home.html')

@login_required(login_url='login')
def dashboard(request):
    auditor_instance = request.user
    return render(request, 'dashboard.html', {'auditor': auditor_instance})

# @login_required(login_url='login')
def admin_dashboard(request):
    if request.user.is_superuser:
        # Perform admin-specific actions or fetch admin-specific data here
        return render(request, 'admin_dashboard.html', {'admin': request.user})
    else:
        # Redirect non-admin users to a different page or display an error message
        return HttpResponse("You are not authorized to access this page.")

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['registrationUsername']
            email = form.cleaned_data['registrationEmail']
            password = form.cleaned_data['registrationPassword']
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

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('adminUsername')
        password = request.POST.get('adminPassword')
        # Authenticate the user against the user database
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            # Check if the authenticated user is a superuser
            login(request, user)
            return redirect('admin_dashboard')  # Redirect to admin dashboard or any admin-specific page
        else:
            return HttpResponse("Invalid username or password.")
    else:
        # Render the admin login page template
        return render(request, 'Home.html')
    
def add_user(request):
    return redirect('register')

@login_required(login_url='login')
def profile(request):
    auditor_instance = request.user
    return render(request,'profile.html',{'auditor': auditor_instance})

# @login_required(login_url='login')
def manage_users(request):
    # Get all users from the database
    users = User.objects.all()
    return render(request, 'manage_users.html', {'users': users})

# @login_required(login_url='login')
def manage_reports(request):
    reports=Report.objects.all()
    return render(request, 'manage_reports.html', {'reports': reports})

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
                    title=generate_title(point)

                for i, point in enumerate(audit_points, start=1):
                    summary = generate_summary(point) 
                    Audit_point_summaries.objects.create(user=request.user, audit_point_text=point, summary=summary)   

                circulars_instance.save()
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
                
                    print("Extracted Text:", extracted_text)

                    # audit_points = split_passages(extracted_text)
                    audit_points = split_points_with_regex(extracted_text)
                    for i, (point, content) in enumerate(audit_points.items(), start=1):
                        print(f"{i}. Point {point}: {content.strip()}")
                        title=extract_title(content)
                        summary = generate_summary(content)  
                        Audit_point_summaries.objects.create(user=request.user, audit_point_text=title,summary=summary)
                    # for i,point in enumerate(audit_points,start=1):
                    #     print(f"Point {i}: {point}")
                    #     title = "" 
                    #     title=extract_title(point)

                    # for i, point in enumerate(audit_points, start=1):
                    #     summary = generate_summary(point) 
                    #     Audit_point_summaries.objects.create(user=request.user, audit_point_text=point, summary=summary)  
                 
                
                # model_path = 'D:\Vedu study\TY\Complaince project\complaince_proj\complaince\model_and_tokenizer.pkl'
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

# def split_points_with_regex(text):
#     extracted_points = {}
#     current_point = None

#     # Regex pattern to match numbered points
#     pattern_numbered = r'\b\d+(\.\d+)?\s*'

#     # Iterate through each line in the text
#     for line in text.split('\n'):
#         # Check if the line starts with a numbered point
#         match_numbered = re.match(pattern_numbered, line)
#         if match_numbered:
#             # Extract the numbered point
#             current_point = match_numbered.group().strip()
#             extracted_points[current_point] = line[len(current_point):].strip()
#         elif line.startswith('('):
#             # If the line starts with parentheses, treat it as a separate point
#             current_point = line.split(':', 1)[0].strip()
#             extracted_points[current_point] = line[len(current_point):].strip()
#         elif current_point:
#             # If no match found and current_point is set, append line to the current point's text
#             extracted_points[current_point] += ' ' + line.strip()

#     return extracted_points

def split_points_with_regex(text):
    extracted_points = {}
    current_point = None

    # Regex pattern to match numbered points
    pattern_numbered = r'\b\d+(\.\d+)?\s*'

    # Split the text at double newline characters to handle passages
    paragraphs = text.strip().split('\n\n')

    # Iterate through each paragraph in the text
    for paragraph in paragraphs:
        lines = paragraph.split('\n')
        # Iterate through each line in the paragraph
        for line in lines:
            # Check if the line starts with a numbered point
            match_numbered = re.match(pattern_numbered, line)
            if match_numbered:
                # Extract the numbered point
                current_point = match_numbered.group().strip()
                extracted_points[current_point] = line[len(current_point):].strip()
            elif line.startswith('('):
                # If the line starts with parentheses, treat it as a separate point
                current_point = line.split(':', 1)[0].strip()
                extracted_points[current_point] = line[len(current_point):].strip()
            elif current_point:
                # If no match found and current_point is set, append line to the current point's text
                extracted_points[current_point] += ' ' + line.strip()
            else:
                # If no current point identified, treat the line as a new point
                current_point = "Unindexed"
                if current_point not in extracted_points:
                    extracted_points[current_point] = ""
                extracted_points[current_point] += ' ' + line.strip()

    return extracted_points

def split_passages(text):
    # point_pattern = re.compile(r'\b\d+\.\d*\s+|[IVXLCDMivxlcdm]+\.\d*\s+')
    # point_pattern = re.compile(r'((?:\d+|[ivxlc]+)\..+?)(?=\s*(?:\b\d+|[ivxlc]+|\(\w+\))\.|$)')
    # point_pattern = re.compile(r'(?:\d+|((?:\d+\.|\d+\.?\d*|I{1,3}\.?|i{1,3}\.?|V?I{0,3}\.?)\s*.*?)\n(?=\s*(?:\d+\.|\d+\.?\d*|I{1,3}\.?|i{1,3}\.?|V?I{0,3}\.?)|$))')
    # point_pattern=re.compile(r'((?:(?:[IVXLCDM]+\.\s)|(?:\d+\.\s)).+?)(?=\n(?:[IVXLCDM]+\.\s|\d+\.\s)|\Z)')
    point_pattern = re.compile(r'(\d+\.[\s\S]*?)(?=\n\d+\.|\Z)|\((?:[ivxlc]+)\)\.[\s\S]*?(?=\n\(\w+\)\.|\Z)')
    audit_points = []
    last_index = 0

    # for match in point_pattern.finditer(text):
    #     index = match.start()
    #     audit_points.append(text[last_index:index].strip())
    #     last_index = match.end()

    for match in point_pattern.finditer(text):
        audit_point = match.group(0).strip()
        audit_points.append(audit_point)

    audit_points.append(text[last_index:].strip())

    return audit_points

# def summarize(text, model, tokenizer, num_sentences=2):
#     input_ids = tokenizer.encode("summarize: " + text, return_tensors="pt", max_length=1024, truncation=True)
    
#     # Generate the summary
#     summary_ids = model.generate(input_ids, max_length=150, min_length=50, num_beams=4, early_stopping=True)
    
#     # Decode the summary from token IDs to human-readable text
#     summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    
#     return summary

def generate_title(passage):
    sentences = sent_tokenize(passage)
    words = [word_tokenize(sentence) for sentence in sentences]
    words_flat = [word for sublist in words for word in sublist]
    word_counts = Counter(words_flat)
    most_common_words = word_counts.most_common(5)
    title = ' '.join(word for word, _ in most_common_words)
    return title

nlp = spacy.load("en_core_web_sm")

def extract_title(passage):
    # Process the passage using spaCy
    doc = nlp(passage)

    # Extract the first sentence
    first_sentence = next(doc.sents, None)
    
    if first_sentence:
        # Extract keywords (nouns and adjectives) from the first sentence
        keywords = [token.text for token in first_sentence if token.pos_ in ['NOUN', 'PROPN', 'ADJ']]
        
        # Construct title from keywords
        if keywords:
            title = " ".join(keywords)
        else:
            title = "Untitled"
    else:
        title = "Untitled"
    
    return title
    
def load_model_and_tokenizer(file_path):
    with open(file_path, 'rb') as model_file:
         model, tokenizer = pickle.load(model_file)
    return model, tokenizer  

def generate_summary(text, num_sentences=2):
    # Tokenize text into sentences
    sentences = sent_tokenize(text)
    
    # Check if the text contains enough meaningful content
    if len(sentences) < num_sentences:
        return "Insufficient content for summary generation."
    
    # Tokenize text into words and remove stopwords
    stop_words = set(stopwords.words("english"))
    words = word_tokenize(text.lower())
    filtered_words = [word for word in words if word.isalnum() and word not in stop_words]
    
    # Check if there are enough meaningful words after stop word removal
    if len(filtered_words) < 5:  # Adjust threshold as needed
        return "Insufficient content for summary generation."
    
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
# def generate_summary(text, num_sentences=2):
#     # Tokenize text into sentences
#     sentences = sent_tokenize(text)
#     # Tokenize text into words
#     words = word_tokenize(text)
#     # Remove stopwords
#     stop_words = set(stopwords.words("english"))
#     filtered_words = [word for word in words if word.lower() not in stop_words]
#     # Compute TF-IDF scores
#     tfidf = TfidfVectorizer()
#     tfidf_matrix = tfidf.fit_transform(sentences)
#     tfidf_matrix = tfidf_matrix.toarray()

#     # Calculate sentence scores based on TF-IDF
#     sentence_scores = np.sum(tfidf_matrix, axis=1)

#     # Select top sentences based on scores
#     top_sentences_indices = sentence_scores.argsort()[-num_sentences:][::-1]
#     top_sentences = [sentences[index] for index in top_sentences_indices]

#     # Combine selected sentences to form the summary
#     summary = ' '.join(top_sentences)

#     return summary


def add_more(request):
    if request.method=='POST':
       form=AnotherUserResponseForm(request.POST)
       if 'addmoreButton' in request.POST:
           if form.is_valid():
              form.instance.user=request.user
              form.save()
              messages.success(request, 'Your response has been saved.')
              return redirect('add_more')
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
    add_more_responses = AddMoreResponse.objects.filter(user=request.user)
    chart_data = pie_chart(user=request.user)
    executive_summary = executive_summary_recommendations(user_responses, add_more_responses)
    # executive_summary=generate_executive_summary(user_responses, add_more_responses,tokenizer, model)
    context = {
        'user_responses': user_responses,
        'add_more_responses': add_more_responses,
        'chart_data': chart_data,
        'executive_summary': executive_summary,
    }
    
    return render(request, 'thank_you.html', context)

def executive_summary_recommendations(user_responses, add_more_responses):  #extravtive summary
    all_recommendations_text = ''
    all_observations_text=''
    
    # Collect recommendations from UserResponse model
    for response in user_responses:
        if response.audit_observations:
            all_observations_text += response.audit_observations + ' '

    for response in user_responses:
        if response.recommandations:
            all_recommendations_text += response.recommandations + ' '

    # Collect recommendations from AddMoreResponse model
    for response in add_more_responses:
        if response.audit_observations:
            all_observations_text += response.audit_observations + ' '
    
    for response in add_more_responses:
        if response.recommandations:
            all_recommendations_text += response.recommandations + ' '
    

    # Tokenize text into sentences
    sentences = sent_tokenize(all_recommendations_text+all_observations_text)

    # Choose a fixed number of sentences for summary
    num_sentences_summary = 2
    summary_sentences = sentences[:num_sentences_summary]

    # Combine summary sentences into a single string
    executive_summary = ' '.join(summary_sentences)

    return executive_summary

def generate_executive_summary(user_responses, add_more_responses, tokenizer, model): #Abstravive way of summary
    all_recommendations_text = ''
    all_observations_text=''
    
    for response in user_responses:
        if response.audit_observations:
            all_observations_text += response.audit_observations + ' '

    for response in user_responses:
        if response.recommandations:
            all_recommendations_text += response.recommandations + ' '
    
    for response in add_more_responses:
        if response.audit_observations:
            all_observations_text += response.audit_observations + ' '

    for response in add_more_responses:
        if response.recommandations:
            all_recommendations_text += response.recommandations + ' '
    
    # Prefix the input text with "summarize:" for abstractive summarization
    input_text = "summarize: " + all_recommendations_text+all_observations_text
    
    # Tokenize the input text
    input_ids = tokenizer.encode(input_text, return_tensors="pt", max_length=1024, truncation=True)
    
    # Generate the summary
    summary_ids = model.generate(input_ids, max_length=150, min_length=50, num_beams=4, early_stopping=True)
    
    # Decode the summary from token IDs to human-readable text
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    
    return summary

    
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
    executive_summary = executive_summary_recommendations(user_responses, add_more_responses)
    # executive_summary=generate_executive_summary(user_responses, add_more_responses,tokenizer, model)
    template = get_template('thank_you.html')
    context = {'user_responses': user_responses,'add_more_responses':add_more_responses,'chart_data':chart_data,'executive_summary': executive_summary,}
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
def rename_report(request, report_id):
    report = Report.objects.get(pk=report_id)
    
    if request.method == 'POST':
        form = RenameReportForm(request.POST, instance=report)
        if form.is_valid():
            # Save the new report name from the form
            report.new_report_name = form.cleaned_data['new_report_name']
            report.save()
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

@login_required(login_url='login')
def audit_points(request):
    audit_points_summaries = Audit_point_summaries.objects.all()
    total_audit_points = audit_points_summaries.count()
    current_index = int(request.GET.get('current_index', 0))
    
    if request.method == 'POST':
        # form = UserResponseForm(request.POST)
        if 'skipButton' in request.POST:
            # If Skip button is clicked, move to the next audit point without saving any response
            current_index += 1
            if current_index < total_audit_points:
                next_url = reverse('audit_points') + f'?current_index={current_index}'
                return redirect(next_url)
            else:
                return redirect('show_report')
        elif 'addmoreButton' in request.POST:
               user_response_form = UserResponseForm(request.POST)
               if user_response_form.is_valid():
                  user_response = user_response_form.save(commit=False)
                  user_response.audit_point = audit_points_summaries[current_index]
                  user_response.user = request.user
                  user_response.save()
                  messages.success(request, 'Your response has been saved.')
                # Redirect to a view where you open the add more response form
                  return redirect('add_moreques')
        elif 'submitButton' in request.POST:
            # If Show button is clicked, redirect to the show report page
            return redirect('show_report')
        else:
            # Next button is clicked, process the form submission
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
                    message = "All audit points are complete. Do you want to add more?"
                    context = {
                        'message': message,
                        'add_more_url': 'add_moreques',
                        'show_report_url': 'show_report'
                    }
                    return render(request, 'pop_up.html', context)
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
    
    return render(request, 'audit_response.html', {'current_audit_point': current_audit_point, 'form': form})

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