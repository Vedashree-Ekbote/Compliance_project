from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count
from .forms import RegistrationForm, UserResponseForm,UploadFileForm,AnotherUserResponseForm,RenameReportForm
from .models import UserResponse, Report,UploadedFile,AddMoreResponse
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
import matplotlib.pyplot as plt
matplotlib.use('Agg')
import pickle,ssl
import re ,subprocess,sys
    
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
                
                model_path = 'D:\\Vedu study\\TY\\Complaince project\\complaince_proj\\complaince\\model.pkl'
                model, tokenizer = load_model_and_tokenizer(model_path)

                passage='''Use of Information Technology by banks has grown rapidly and is now an important part of the operational strategy of banks. The
                           number, frequency and impact of cyber incidents/attacks have
                            increased manifold in the recent past, more so in the case of
financial sector including banks. There is an urgent need to put in place a robust cyber security/resilience framework at UCBs to
ensure adequate security of their assets on a continuous basis. It
has, therefore, become essential to enhance the security of the
UCBs from cyber threats by improving the current defenses in
addressing cyber risks.'''

                summary=summarize(passage, model, tokenizer)
                print("Generated Summary:\n",summary)
                # text extraction
                # circulars_instance = UploadedFile.objects.filter(user=request.user)
                # extracted_text = ''

                # for uploaded_file in circulars_instance:
                #     pdf_path = uploaded_file.file.path
                #     images = convert_pdf_to_images(pdf_path)

                #     for i, image in enumerate(images):
                #         image_path = f"temp_image_{i}.png"
                #         image.save(image_path, "PNG")
                #         text = extracted_text_from_img(image_path)
                #         extracted_text += f"Page {i + 1}:\n{text}\n{'-' * 40}\n"
                
                # text_file_path='C:\Users\Admin\Desktop\ANA Cyber Forensics wrk\complaince_proj\complaince\media\extracted_text.txt'
                # with open(output_file_path, 'r') as output_file:
                #     processed_results = output_file.read()     

                # colab_notebook_path="C:\Users\Admin\Desktop\ANA Cyber Forensics wrk\complaince_proj\complaince\Summeizer.ipynb"    
                # with open(text_file_path, 'w') as text_file:
                #      text_file.write(extracted_text)

                # output_file_path = 'C:\Users\Admin\Desktop\ANA Cyber Forensics wrk\complaince_proj\complaince\media\output.txt'
                
                # Execute the Colab notebook using subprocess
                # subprocess.run(['jupyter', 'nbconvert', '--execute', '--to', 'notebook', '--output', 'output.ipynb', colab_notebook_path, '--ExecutePreprocessor.allow_errors=True', '--ExecutePreprocessor.timeout=-1'])

                # Read the processed results from the output file
               
                # splitting the text into different passages
                # passage_pattern = re.compile(r'(\d+(\.\d+)?|[IVXLCDM]+)\.\s+(.*)', re.DOTALL)
                # # passage_pattern = re.compile(r'(\d+\.\d+|\d+\.|[IVXLCDM]+|\s+)(.*?)(?=\n\n(?:\d+\.\d+|\d+\.|[IVXLCDM]+|\s+|$)|\Z)', re.DOTALL)
                # matches = passage_pattern.findall(extracted_text)
                # passages = [(match[0].strip(), match[1].strip()) for match in matches if match[1].strip()]

                # for i, passage in enumerate(passages):
                #     entire_point, text_part = passage
                #     print(f"Passage {i + 1} - Entire Point:\n{entire_point}")
                #     print(f"Passage {i + 1} - Text Part:\n{text_part}\n")

                return redirect('genreport')
            else:
                return HttpResponse("Invalid Form")

    else:
        form = UploadFileForm()

    return render(request, 'genreport.html', {'form': form}) 

def summarize(text, model, tokenizer):
    summarizer = pipeline("summarization", model=model, tokenizer=tokenizer)
    summary = summarizer(text, max_length=150, min_length=50, length_penalty=2.0, num_beams=4, early_stopping=True)[0]['summary_text']
    return summary

def load_model_and_tokenizer(file_path):
    with open(file_path, 'rb') as model_file:
         model, tokenizer = pickle.load(model_file)
    return model, tokenizer

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
    chart_data=pie_chart(user=request.user)
    context={
     'user_responses':user_responses,
     'add_more_responses':add_more_responses,
     'chart_data': chart_data
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
    chart_data=pie_chart(user=request)
    template = get_template('results.html')
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
    
    for entry in combined_counts:
        if entry['compliance_type'] == 'compliant':
            compliant_count += entry['count']
        elif entry['compliance_type'] == 'partially-compliant':
            partially_compliant_count += entry['count']
        elif entry['compliance_type'] == 'non-compliant':
            non_compliant_count += entry['count']
    total_count = compliant_count + partially_compliant_count + non_compliant_count

    # Calculate percentages
    compliant_percentage = (compliant_count / total_count) * 100
    partially_compliant_percentage = (partially_compliant_count / total_count) * 100
    non_compliant_percentage = (non_compliant_count / total_count) * 100

    if total_count == 0:
        print("No data available for pie chart.")
        return None
    data = [compliant_count, partially_compliant_count, non_compliant_count]
    labels = [f"Compliant ({compliant_percentage:.2f}%)", f"Partially Compliant ({partially_compliant_percentage:.2f}%)", f"Non-Compliant ({non_compliant_percentage:.2f}%)"]

    # Create pie chart
    plt.pie(data, labels=labels, colors=['green', '#FFC200', 'red'])
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
    return render(request,'audit_questionare.html')

def add_moreques(request):
    return render(request,'Add_more.html')

@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('form')
