from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class GmailAccount(models.Model):
    """Stores Gmail account connection info."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(unique=True)
    token_file = models.TextField(blank=True, null=True)
    connected_at = models.DateTimeField(auto_now_add=True)
    last_sync = models.DateTimeField(auto_now=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.email}"
    
    class Meta:
        verbose_name = "Gmail Account"
        verbose_name_plural = "Gmail Accounts"


class EmailMessage(models.Model):
    EMAIL_RISK_LEVELS = [
        ('SAFE', 'Safe'),
        ('LOW', 'Low Risk'),
        ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'),
        ('CRITICAL', 'Critical Risk')
    ]
    """Stores scanned email messages."""
    gmail_account = models.ForeignKey(GmailAccount, on_delete=models.CASCADE, related_name='messages')
    message_id = models.CharField(max_length=255, unique=True)
    subject = models.TextField()
    sender = models.EmailField()
    received_date = models.DateTimeField()
    body_text = models.TextField()
    snippet = models.TextField(blank=True)
    scanned_at = models.DateTimeField(auto_now_add=True)
    
    # Analysis results
    is_phishing = models.BooleanField(default=False)
    is_ai_generated = models.BooleanField(default=False)
    risk_level = models.CharField(max_length=20, choices=EMAIL_RISK_LEVELS, default='SAFE')
    
    def __str__(self):
        return f"{self.subject[:50]} - {self.sender}"
    
    class Meta:
        verbose_name = "Email Message"
        verbose_name_plural = "Email Messages"
        ordering = ['-received_date']


class LinkAnalysis(models.Model):
    LINK_RISK_LEVEL = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical')
    ]
    """Stores analysis results for links found in emails."""
    email = models.ForeignKey(EmailMessage, on_delete=models.CASCADE, related_name='links')
    url = models.URLField(max_length=2048)
    
    # Analysis results
    is_suspicious = models.BooleanField(default=False)
    risk_score = models.IntegerField(default=0)
    risk_level = models.CharField(max_length=20, choices=LINK_RISK_LEVEL, default='LOW')
    
    # Detailed findings
    indicators = models.JSONField(default=list)
    details = models.JSONField(default=dict)
    
    analyzed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.url[:50]} - {self.risk_level}"
    
    class Meta:
        verbose_name = "Link Analysis"
        verbose_name_plural = "Link Analyses"


class AIDetectionResult(models.Model):
    """Stores AI detection results for email text."""
    email = models.OneToOneField(EmailMessage, on_delete=models.CASCADE, related_name='ai_detection')
    is_ai_generated = models.BooleanField(default=False)
    confidence_score = models.FloatField(default=0.0)
    confidence_level = models.CharField(max_length=50)
    
    # Detailed scores
    perplexity_score = models.FloatField(default=0.0)
    burstiness_score = models.FloatField(default=0.0)
    pattern_score = models.FloatField(default=0.0)
    uniformity_score = models.FloatField(default=0.0)
    indicators = models.JSONField(default=list)
    analyzed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.email.subject[:30]} - AI: {self.is_ai_generated}"
    
    class Meta:
        verbose_name = "AI Detection Result"
        verbose_name_plural = "AI Detection Results"


class ScanHistory(models.Model):
    STATUS_CHOICES = [
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    """Tracks scanning operations."""
    gmail_account = models.ForeignKey(GmailAccount, on_delete=models.CASCADE, related_name='scans')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    total_emails = models.IntegerField(default=0)
    safe_emails = models.IntegerField(default=0)
    phishing_emails = models.IntegerField(default=0)
    ai_generated_emails = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RUNNING')
    error_message = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Scan {self.id} - {self.started_at.strftime('%d-%m-%Y %H:%M')}"
    
    class Meta:
        verbose_name = "Scan History"
        verbose_name_plural = "Scan Histories"
        ordering = ['-started_at']


class ThreatStatistics(models.Model):
    """Aggregated statistics for dashboard."""
    gmail_account = models.ForeignKey(GmailAccount, on_delete=models.CASCADE)
    
    date = models.DateField(default=timezone.now)
    
    total_emails_scanned = models.IntegerField(default=0)
    safe_count = models.IntegerField(default=0)
    phishing_count = models.IntegerField(default=0)
    ai_phishing_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Threat Statistics"
        verbose_name_plural = "Threat Statistics"
        unique_together = ['gmail_account', 'date']
        ordering = ['-date']