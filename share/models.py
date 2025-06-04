from django.db import models

class SharedDocument(models.Model):
    public_ip = models.GenericIPAddressField(unique=True)
    content = models.TextField(default="")
    local_ip = models.GenericIPAddressField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Text for Public IP: {self.public_ip} (Local: {self.local_ip or 'N/A'})"

class SharedImage(models.Model):
    image = models.ImageField(upload_to='shared_images/')
    public_ip = models.GenericIPAddressField()
    local_ip = models.GenericIPAddressField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image from {self.public_ip} (Local: {self.local_ip or 'N/A'}) at {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-uploaded_at']