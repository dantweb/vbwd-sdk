import re
from typing import List, Optional


class ValidatorService:
    """Validation service for submissions."""

    ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    def validate_submission(self, data: dict) -> List[str]:
        """Validate submission data. Returns list of errors."""
        errors = []

        # Email validation
        email_error = self._validate_email(data.get('email'))
        if email_error:
            errors.append(email_error)

        # Consent validation
        if not data.get('consent'):
            errors.append('Consent is required')

        # Images validation
        images_errors = self._validate_images(data.get('images', []))
        errors.extend(images_errors)

        return errors

    def _validate_email(self, email: Optional[str]) -> Optional[str]:
        if not email:
            return 'Email is required'
        if not re.match(self.EMAIL_REGEX, email):
            return 'Invalid email format'
        return None

    def _validate_images(self, images: list) -> List[str]:
        errors = []
        if not images:
            errors.append('At least one image is required')
            return errors

        for i, img in enumerate(images):
            if img.get('type') not in self.ALLOWED_IMAGE_TYPES:
                errors.append(f'Image {i+1}: Invalid format. Allowed: JPEG, PNG, WebP')
            if img.get('size', 0) > self.MAX_IMAGE_SIZE:
                errors.append(f'Image {i+1}: Exceeds 10MB limit')

        return errors
