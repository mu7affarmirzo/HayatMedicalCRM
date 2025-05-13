# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages

from core.models import IllnessHistory, Document, AssignedLabResult


@login_required
def documents_view(request, pk):
    """Main view for documents related to an illness history"""
    history = get_object_or_404(IllnessHistory, pk=pk)

    # Get all documents and categorize them
    all_documents = Document.objects.filter(illness_history=history).order_by('-created_at')
    medical_results = AssignedLabResult.objects.filter(assigned_lab__illness_history=history).order_by('-created_at')
    consents = all_documents.filter(category='consents')
    reports = all_documents.filter(category='reports')

    context = {
        'history': history,
        'all_documents': all_documents,
        'medical_results': medical_results,
        'consents': consents,
        'reports': reports,
        'active_page': {'documents_page': 'active'}
    }

    return render(request, 'sanatorium/nurses/documents/documents_page.html', context)


@login_required
@require_POST
def document_upload(request, pk):
    """Handle document upload via AJAX"""
    history = get_object_or_404(IllnessHistory, pk=pk)

    if request.FILES.get('file'):
        uploaded_file = request.FILES['file']

        # Check file size (max 10MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'error': 'Файл слишком большой. Максимальный размер 10 МБ.'
            })

        # Get file type
        file_name = uploaded_file.name
        file_ext = file_name.split('.')[-1].lower()

        # Validate file type
        allowed_extensions = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'xls', 'xlsx']
        if file_ext not in allowed_extensions:
            return JsonResponse({
                'success': False,
                'error': 'Недопустимый тип файла. Разрешены только PDF, DOC, DOCX, JPG, PNG, XLS, XLSX.'
            })

        # Determine file type category for display
        if file_ext in ['jpg', 'jpeg', 'png']:
            file_type = 'image'
        else:
            file_type = file_ext

        # Create document object
        document = Document.objects.create(
            illness_history=history,
            file=uploaded_file,
            name=file_name,
            file_type=file_type,
            category=request.POST.get('category', 'other'),
            description=request.POST.get('description', ''),
            uploaded_by=request.user,
            size=f"{uploaded_file.size / 1024:.1f} KB" if uploaded_file.size < 1024 * 1024 else f"{uploaded_file.size / (1024 * 1024):.1f} MB"
        )

        return JsonResponse({
            'success': True,
            'document_id': document.id,
            'message': 'Файл успешно загружен'
        })

    return JsonResponse({
        'success': False,
        'error': 'Файл не был получен'
    })


@login_required
@require_POST
def document_delete(request, document_id):
    """Delete a document"""
    document = get_object_or_404(Document, id=document_id)
    history_id = document.illness_history.id

    # Check if user has permission (either uploaded the doc or is admin)
    if document.uploaded_by == request.user or request.user.is_staff:
        document_name = document.name
        document.delete()
        messages.success(request, f'Документ "{document_name}" успешно удален.')
    else:
        messages.error(request, 'У вас нет прав для удаления этого документа.')

    return redirect('documents_view', history_id=history_id)
