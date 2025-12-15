"""Test fixtures for submissions."""


def valid_submission():
    """Return a valid submission data dict."""
    return {
        'email': 'test@example.com',
        'consent': True,
        'images': [
            {
                'type': 'image/jpeg',
                'size': 1024,
                'data': 'data:image/jpeg;base64,/9j/4AAQSkZJRg...'
            }
        ],
        'comments': 'Test submission for diagnostic analysis'
    }


def submission_without_email():
    """Return submission data without email."""
    data = valid_submission()
    del data['email']
    return data


def submission_without_consent():
    """Return submission data without consent."""
    data = valid_submission()
    data['consent'] = False
    return data


def submission_without_images():
    """Return submission data without images."""
    data = valid_submission()
    data['images'] = []
    return data


def submission_with_invalid_image_type():
    """Return submission data with invalid image type."""
    data = valid_submission()
    data['images'] = [{'type': 'image/gif', 'size': 1024}]
    return data


def submission_with_large_image():
    """Return submission data with image exceeding size limit."""
    data = valid_submission()
    data['images'] = [{'type': 'image/jpeg', 'size': 15 * 1024 * 1024}]  # 15MB
    return data


def submission_with_multiple_images():
    """Return submission data with multiple images."""
    data = valid_submission()
    data['images'] = [
        {'type': 'image/jpeg', 'size': 1024, 'data': 'base64...'},
        {'type': 'image/png', 'size': 2048, 'data': 'base64...'},
        {'type': 'image/webp', 'size': 512, 'data': 'base64...'}
    ]
    return data
