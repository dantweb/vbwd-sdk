from flask import Blueprint, request, jsonify, current_app
from src.services.submission_service import SubmissionService
from src.services.validator_service import ValidatorService
from src import db, executor

user_bp = Blueprint('user', __name__)


@user_bp.route('/submit', methods=['POST'])
def submit_diagnostic():
    """
    Fire-and-Forget submission endpoint.
    Returns 202 immediately, processes in background.
    """
    data = request.get_json()

    # 1. Validate (sync, fast)
    validator = ValidatorService()
    errors = validator.validate_submission(data)
    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    # 2. Create submission record (sync, fast)
    service = SubmissionService(db.session)
    submission = service.create_submission(data)

    # 3. Submit to background thread (non-blocking)
    app = current_app._get_current_object()
    executor.submit(
        service.process_submission_background,
        app,
        submission.id,
        data
    )

    # 4. Return immediately
    return jsonify({
        "success": True,
        "message": "Your data is submitted. You will receive results via email.",
        "submission_id": submission.id
    }), 202


@user_bp.route('/status/<int:submission_id>', methods=['GET'])
def get_status(submission_id):
    """Get submission status (for polling if WebSocket not available)."""
    service = SubmissionService(db.session)
    submission = service.get_submission(submission_id)

    if not submission:
        return jsonify({"success": False, "message": "Not found"}), 404

    return jsonify({
        "success": True,
        "submission_id": submission.id,
        "status": submission.status,
        "created_at": submission.created_at.isoformat() if submission.created_at else None
    }), 200
