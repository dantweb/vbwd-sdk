from src import db
from datetime import datetime


class Submission(db.Model):
    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, index=True)
    status = db.Column(
        db.Enum('pending', 'processing', 'completed', 'failed'),
        default='pending',
        index=True
    )
    images_data = db.Column(db.JSON)
    comments = db.Column(db.Text)
    consent_given = db.Column(db.Boolean, default=False)
    consent_timestamp = db.Column(db.DateTime)
    result = db.Column(db.JSON)
    error = db.Column(db.Text)
    loopai_execution_id = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'status': self.status,
            'comments': self.comments,
            'consent_given': self.consent_given,
            'loopai_execution_id': self.loopai_execution_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def to_dict_full(self):
        """Full dict including result (for admin)."""
        data = self.to_dict()
        data['images_data'] = self.images_data
        data['result'] = self.result
        data['error'] = self.error
        return data
