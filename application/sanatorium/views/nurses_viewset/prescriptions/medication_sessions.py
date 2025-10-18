from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from HayatMedicalCRM.auth.decorators import nurse_required
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
import json

# Assuming these are your model imports based on the paste.txt
from core.models import MedicationSession, PrescribedMedication


@method_decorator([nurse_required, csrf_exempt], name='dispatch')
class MedicationSessionUpdateStatusView(View):
    """
    API endpoint to update medication session status
    """

    def post(self, request, session_id):
        try:
            # Get the session
            session = get_object_or_404(MedicationSession, id=session_id)

            # Parse request data
            data = json.loads(request.body)
            new_status = data.get('status')
            notes = data.get('notes', '')

            # Validate status
            valid_statuses = [choice[0] for choice in MedicationSession.STATUS_CHOICES]
            if new_status not in valid_statuses:
                return JsonResponse({
                    'success': False,
                    'error': f'Недопустимый статус: {new_status}'
                }, status=400)

            # Update session
            session.status = new_status
            if notes:
                session.notes = notes

            # Set who modified it
            session.modified_by = request.user
            session.modified_at = timezone.now()

            # Save the session
            session.save()

            # Return updated session data
            return JsonResponse({
                'success': True,
                'message': 'Статус сессии успешно обновлен',
                'session': {
                    'id': session.id,
                    'status': session.status,
                    'status_display': session.get_status_display(),
                    'notes': session.notes,
                    'modified_by': session.modified_by.full_name if session.modified_by else None,
                    'modified_at': session.modified_at.strftime('%d.%m.%Y %H:%M') if session.modified_at else None
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Неверный формат JSON'
            }, status=400)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Произошла ошибка: {str(e)}'
            }, status=500)


@method_decorator([nurse_required, csrf_exempt], name='dispatch')
class MedicationSessionUpdateNotesView(View):
    """
    API endpoint to update medication session notes
    """

    def post(self, request, session_id):
        try:
            # Get the session
            session = get_object_or_404(MedicationSession, id=session_id)

            # Parse request data
            data = json.loads(request.body)
            notes = data.get('notes', '')

            # Update session notes
            session.notes = notes

            # Set who modified it
            session.modified_by = request.user
            session.modified_at = timezone.now()

            # Save the session
            session.save()

            return JsonResponse({
                'success': True,
                'message': 'Примечания успешно сохранены',
                'session': {
                    'id': session.id,
                    'notes': session.notes,
                    'modified_by': session.modified_by.full_name if session.modified_by else None,
                    'modified_at': session.modified_at.strftime('%d.%m.%Y %H:%M') if session.modified_at else None
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Неверный формат JSON'
            }, status=400)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Произошла ошибка: {str(e)}'
            }, status=500)


# Alternative function-based views (if you prefer this approach)

@nurse_required
@csrf_exempt
@require_http_methods(["POST"])
def update_medication_session_status(request, session_id):
    """
    Function-based view to update medication session status
    """
    try:
        # Get the session
        session = get_object_or_404(MedicationSession, id=session_id)

        # Parse request data
        data = json.loads(request.body)
        new_status = data.get('status')
        notes = data.get('notes', '')

        # Validate status
        valid_statuses = [choice[0] for choice in MedicationSession.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return JsonResponse({
                'success': False,
                'error': f'Недопустимый статус: {new_status}'
            }, status=400)

        # Update session
        session.status = new_status
        if notes:
            session.notes = notes

        # Set who modified it
        session.modified_by = request.user
        session.modified_at = timezone.now()

        # Save the session
        session.save()

        # Return updated session data
        return JsonResponse({
            'success': True,
            'message': 'Статус сессии успешно обновлен',
            'session': {
                'id': session.id,
                'status': session.status,
                'status_display': session.get_status_display(),
                'notes': session.notes,
                'modified_by': session.modified_by.full_name if session.modified_by else None,
                'modified_at': session.modified_at.strftime('%d.%m.%Y %H:%M') if session.modified_at else None
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Неверный формат JSON'
        }, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Произошла ошибка: {str(e)}'
        }, status=500)


@nurse_required
@csrf_exempt
@require_http_methods(["POST"])
def update_medication_session_notes(request, session_id):
    """
    Function-based view to update medication session notes
    """
    try:
        # Get the session
        session = get_object_or_404(MedicationSession, id=session_id)

        # Parse request data
        data = json.loads(request.body)
        notes = data.get('notes', '')

        # Update session notes
        session.notes = notes

        # Set who modified it
        session.modified_by = request.user
        session.modified_at = timezone.now()

        # Save the session
        session.save()

        return JsonResponse({
            'success': True,
            'message': 'Примечания успешно сохранены',
            'session': {
                'id': session.id,
                'notes': session.notes,
                'modified_by': session.modified_by.full_name if session.modified_by else None,
                'modified_at': session.modified_at.strftime('%d.%m.%Y %H:%M') if session.modified_at else None
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Неверный формат JSON'
        }, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Произошла ошибка: {str(e)}'
        }, status=500)