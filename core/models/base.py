from uuid import uuid4
from django.conf import settings
from django.db import models



STATE_CHOICES = (
    ('Приём завершён', 'Приём завершён'),
    ('Пациент на прием не явился', 'Пациент на прием не явился'),
    ('Не завершено', 'Не завершено'),
)



class UnsupportedFormat(Exception):
    pass


def upload_lab_files_location(instance, filename):
    ext = filename.split('.')[-1]
    if ext.lower() in ['doc', 'docx', 'xls', 'png', 'pdf', 'xml', 'jpeg', 'mp4', 'jpg', 'mov', 'm4v', 'csv']:
        file_path = f"files/labs/{uuid4().hex}.{ext}"
        return file_path
    else:
        raise UnsupportedFormat(f"The file format '{ext}' is not supported. Supported formats are: doc, docx, png, pdf, xml, jpeg, mp4, jpg, mov, m4v.")


def upload_location(instance, filename):
    ext = filename.split('.')[-1]
    if ext.lower() in ['doc', 'png', 'pdf', 'xml', 'jpeg', 'mp4', 'jpg', 'mov', 'm4v']:
        file_path = f"files/img/{uuid4().hex}.{ext}"
        return file_path
    else:
        raise UnsupportedFormat(f"The file format '{ext}' is not supported. Supported formats are: doc, docx, png, pdf, xml, jpeg, mp4, jpg, mov, m4v.")


def upload_documents_location(instance, filename):
    ext = filename.split('.')[-1]
    if ext.lower() in ['doc', 'png', 'pdf', 'xml', 'jpeg', 'mp4', 'jpg', 'mov', 'm4v']:
        file_path = f"files/documents/{uuid4().hex}.{ext}"
        return file_path
    else:
        raise UnsupportedFormat(f"The file format '{ext}' is not supported. Supported formats are: doc, docx, png, pdf, xml, jpeg, mp4, jpg, mov, m4v.")


class BaseAuditModel(models.Model):
    """
    Abstract base model that provides audit fields for all models
    """
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_modified"
    )

    class Meta:
        abstract = True
