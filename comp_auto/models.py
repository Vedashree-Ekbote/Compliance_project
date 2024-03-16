from django.db import models
from django.contrib.auth.models import User
# from comp_auto.models import User

# # Create your models here.
# class UserProfile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     phone_number = models.CharField(max_length=10, blank=True, null=True) 

#     def __str__(self):
#         return self.user.username

#Model To Store User Responses
class UserResponse(models.Model):

    user = models.ForeignKey(User,on_delete=models.CASCADE, default=1)

    COMPLIANCE_CHOICES = (
        ('compliant', 'Compliant'),
        ('partially-compliant', 'Partially Compliant'),
        ('non-compliant', 'Non-Compliant'),
        ('not-applicable','Not-applicable'),
    )
    
    compliance_type = models.CharField(
          max_length=20,
          choices=COMPLIANCE_CHOICES
    )
    audit_observations =models.TextField()
    recommandations=models.TextField()
    
    # summary = models.TextField(blank=True, null=True,editable=False)
    def __str__(self):
        return f"UserResponse - ID: {self.id}"
    
class AddMoreResponse(models.Model):

    user = models.ForeignKey(User,on_delete=models.CASCADE, default=1)
    
    title = models.TextField(max_length=255)

    Summary=models.TextField()

    COMPLIANCE_CHOICES = (
        ('compliant', 'Compliant'),
        ('partially-compliant', 'Partially Compliant'),
        ('non-compliant', 'Non-Compliant'),
        ('not-applicable','Not-applicable'),
    )
    
    compliance_type = models.CharField(
          max_length=20,
          choices=COMPLIANCE_CHOICES
    )
    audit_observations =models.TextField()

    recommandations=models.TextField()

    def __str__(self):
        return f"AddMoreResponse - ID: {self.id}"

#Model to Store the reports
class Report(models.Model):
     user = models.ForeignKey(User,on_delete=models.CASCADE, default=1)
     pdf_file=models.FileField(upload_to='pdf_reports/')
     created_at=models.DateTimeField(auto_now_add=True)

     def __str__(self):
        return f"Report for {self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
     
class UploadedFile(models.Model):
      user = models.ForeignKey(User,on_delete=models.CASCADE, default=1)
      file=models.FileField(upload_to='uploaded_files/')
      uploaded_at=models.DateTimeField(auto_now_add=True)

      def __str__(self):
          return self.file.name
      
class Audit_point_summaries(models.Model):
      user=models.ForeignKey(User,on_delete=models.CASCADE,default=1)
      audit_point_text=models.TextField()
      summary=models.TextField(max_length=255)

      def __str__(self):
        return self.audit_point_text