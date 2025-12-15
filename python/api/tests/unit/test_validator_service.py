import pytest
from src.services.validator_service import ValidatorService


class TestValidatorService:
    """Unit tests for ValidatorService - TDD first."""

    def setup_method(self):
        self.validator = ValidatorService()

    def test_valid_submission_passes(self):
        """Valid submission should have no errors."""
        data = {
            'email': 'test@example.com',
            'consent': True,
            'images': [{'type': 'image/jpeg', 'size': 1000}]
        }
        errors = self.validator.validate_submission(data)
        assert errors == []

    def test_missing_email_fails(self):
        """Missing email should return error."""
        data = {'consent': True, 'images': [{'type': 'image/jpeg', 'size': 1000}]}
        errors = self.validator.validate_submission(data)
        assert 'Email is required' in errors

    def test_invalid_email_fails(self):
        """Invalid email format should return error."""
        data = {
            'email': 'not-an-email',
            'consent': True,
            'images': [{'type': 'image/jpeg', 'size': 1000}]
        }
        errors = self.validator.validate_submission(data)
        assert 'Invalid email format' in errors

    def test_missing_consent_fails(self):
        """Missing consent should return error."""
        data = {
            'email': 'test@example.com',
            'consent': False,
            'images': [{'type': 'image/jpeg', 'size': 1000}]
        }
        errors = self.validator.validate_submission(data)
        assert 'Consent is required' in errors

    def test_no_images_fails(self):
        """No images should return error."""
        data = {'email': 'test@example.com', 'consent': True, 'images': []}
        errors = self.validator.validate_submission(data)
        assert 'At least one image is required' in errors

    def test_invalid_image_type_fails(self):
        """Invalid image type should return error."""
        data = {
            'email': 'test@example.com',
            'consent': True,
            'images': [{'type': 'image/gif', 'size': 1000}]
        }
        errors = self.validator.validate_submission(data)
        assert any('Invalid format' in e for e in errors)

    def test_image_too_large_fails(self):
        """Image exceeding size limit should return error."""
        data = {
            'email': 'test@example.com',
            'consent': True,
            'images': [{'type': 'image/jpeg', 'size': 20 * 1024 * 1024}]  # 20MB
        }
        errors = self.validator.validate_submission(data)
        assert any('Exceeds 10MB' in e for e in errors)

    def test_multiple_valid_images_pass(self):
        """Multiple valid images should pass."""
        data = {
            'email': 'test@example.com',
            'consent': True,
            'images': [
                {'type': 'image/jpeg', 'size': 1000},
                {'type': 'image/png', 'size': 2000},
                {'type': 'image/webp', 'size': 3000}
            ]
        }
        errors = self.validator.validate_submission(data)
        assert errors == []

    def test_multiple_errors_returned(self):
        """Multiple validation failures should return multiple errors."""
        data = {
            'email': '',
            'consent': False,
            'images': []
        }
        errors = self.validator.validate_submission(data)
        assert len(errors) >= 3
