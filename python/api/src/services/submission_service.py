from src.models.submission import Submission
from src.services.loopai_client import LoopAIClient
from src.services.email_service import EmailService
from src import db, socketio
from datetime import datetime


class SubmissionService:
    """
    Service for handling diagnostic submissions.
    Follows Single Responsibility Principle - only handles submission logic.
    Dependencies injected via constructor (DI).
    """

    def __init__(self, db_session, loopai_client=None, email_service=None):
        self._db = db_session
        self._loopai = loopai_client or LoopAIClient()
        self._email = email_service or EmailService()

    def create_submission(self, data: dict) -> Submission:
        """Create new submission record."""
        submission = Submission(
            email=data['email'],
            images_data=data.get('images'),
            comments=data.get('comments'),
            consent_given=data.get('consent', False),
            consent_timestamp=datetime.utcnow() if data.get('consent') else None,
            status='pending'
        )
        self._db.add(submission)
        self._db.commit()
        return submission

    def get_submission(self, submission_id: int) -> Submission:
        """Get submission by ID."""
        return Submission.query.get(submission_id)

    def list_submissions(self, page: int, per_page: int, status: str = None) -> dict:
        """List submissions with pagination and optional status filter."""
        query = Submission.query
        if status:
            query = query.filter_by(status=status)

        query = query.order_by(Submission.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page)

        return {
            'items': [s.to_dict() for s in pagination.items],
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total
        }

    def process_submission_background(self, app, submission_id: int, data: dict):
        """
        Background processing - runs in ThreadPoolExecutor.
        Does NOT block HTTP requests.
        """
        with app.app_context():
            try:
                submission = Submission.query.get(submission_id)
                submission.status = 'processing'
                db.session.commit()

                # Notify frontend (if connected)
                self._emit_status(submission, 'Processing your submission...')

                # Call LoopAI API
                response = self._loopai.run_diagnostic(data)
                submission.loopai_execution_id = response.get('execution_id')
                db.session.commit()

                # Poll for results
                result = self._loopai.poll_for_result(response['execution_id'])

                # Update submission
                submission.status = 'completed'
                submission.result = result
                db.session.commit()

                # Send email
                self._email.send_result(submission.email, result)

                # Notify frontend
                self._emit_status(submission, 'Your results are ready! Check your email.')

            except Exception as e:
                submission = Submission.query.get(submission_id)
                submission.status = 'failed'
                submission.error = str(e)
                db.session.commit()
                self._emit_status(submission, f'Error processing submission: {str(e)}')

    def _emit_status(self, submission: Submission, message: str):
        """Emit WebSocket status update."""
        try:
            socketio.emit('status_update', {
                'submission_id': submission.id,
                'status': submission.status,
                'message': message
            }, room=f'user_{submission.email}')
        except Exception as e:
            print(f'WebSocket emit error: {e}')
