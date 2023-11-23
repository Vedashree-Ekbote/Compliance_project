from django.contrib import admin

# Register your models here.
from .models import UserResponse
from .models import Report
from .models import UploadedFile
from .models import AddMoreResponse

admin.site.register(UserResponse)
admin.site.register(Report)
admin.site.register(UploadedFile)
admin.site.register(AddMoreResponse)
