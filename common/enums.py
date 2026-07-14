from django.db import models

class OTPPurposeChoice(models.TextChoices):
    SIGN_UP = "SIGNUP", "Sign Up"
    LOGIN = "LOGIN", "Login"
    PASSWORD_RESET = "PASSWORD_RESET", "Password reset"
