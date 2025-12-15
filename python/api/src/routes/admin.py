from flask import Blueprint, request, jsonify
from functools import wraps
from src.services.submission_service import SubmissionService
from src.services.auth_service import AuthService
from src import db

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = AuthService()
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not auth.verify_admin_token(token):
            return jsonify({"success": False, "message": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/submissions', methods=['GET'])
@admin_required
def list_submissions():
    """List all submissions with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')

    service = SubmissionService(db.session)
    result = service.list_submissions(page, per_page, status)

    return jsonify({
        "success": True,
        "data": result['items'],
        "pagination": {
            "page": result['page'],
            "per_page": result['per_page'],
            "total": result['total']
        }
    }), 200


@admin_bp.route('/submissions/<int:submission_id>', methods=['GET'])
@admin_required
def get_submission(submission_id):
    """Get single submission details."""
    service = SubmissionService(db.session)
    submission = service.get_submission(submission_id)

    if not submission:
        return jsonify({"success": False, "message": "Not found"}), 404

    return jsonify({
        "success": True,
        "data": submission.to_dict()
    }), 200
