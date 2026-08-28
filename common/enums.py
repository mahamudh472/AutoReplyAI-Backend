from django.db import models

class OTPPurposeChoice(models.TextChoices):
    SIGN_UP = "SIGNUP", "Sign Up"
    LOGIN = "LOGIN", "Login"
    PASSWORD_RESET = "PASSWORD_RESET", "Password reset"

class PlatformChoice(models.TextChoices):
    FACEBOOK_PAGE = "FACEBOOK_PAGE", "Facebook Page"
    INSTAGRAM = "INSTAGRAM", "Instagram"
    WHATSAPP_BUSINESS = "WHATSAPP_BUSINESS", "WhatsApp Business"

class OrganizationRoleChoice(models.TextChoices):
    OWNER = "OWNER", "Owner"
    ADMIN = "ADMIN", "Admin"
    MEMBER = "MEMBER", "Member"

class KnowledgeDocumentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    INDEXED = "indexed", "Indexed"
    FAILED = "failed", "Failed"

class KnowledgeSourceType(models.TextChoices):
    FILE = "file", "File Upload"
    TEXT = "text", "Raw Text"
    FAQ = "faq", "FAQ"
    URL = "url", "Web Page URL"



