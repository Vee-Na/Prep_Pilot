from django.db import models
from django.contrib.auth.models import AbstractUser

class Role(models.TextChoices):

    ADMIN='Admin','Admin'
    INTERVIEWEE='Interviewee','Interviewee'

class Profile(AbstractUser):

    role=models.CharField(max_length=20,choices=Role.choices,default=Role.INTERVIEWEE)
    email=models.EmailField(unique=True)

    class Meta:
        verbose_name='Profiles'
        verbose_name_plural='Profiles'

    def __str__(self):
        return f'{self.username}-{self.role}'
