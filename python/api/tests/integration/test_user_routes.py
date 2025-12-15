import pytest


class TestHealthEndpoint:
    """Integration tests for health endpoint."""

    def test_health_check_returns_200(self, client):
        """Health check should return 200 when healthy."""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'


class TestUserRoutes:
    """Integration tests for user API routes."""

    def test_submit_returns_202(self, client, sample_submission_data):
        """Submission should return 202 Accepted (fire-and-forget)."""
        response = client.post(
            '/api/user/submit',
            json=sample_submission_data,
            content_type='application/json'
        )
        assert response.status_code == 202
        result = response.get_json()
        assert result['success'] is True
        assert 'submission_id' in result

    def test_submit_invalid_data_returns_400(self, client):
        """Invalid submission should return 400."""
        data = {'email': 'invalid'}  # Missing required fields
        response = client.post(
            '/api/user/submit',
            json=data,
            content_type='application/json'
        )
        assert response.status_code == 400
        result = response.get_json()
        assert result['success'] is False
        assert 'errors' in result

    def test_submit_missing_consent_returns_400(self, client):
        """Missing consent should return 400."""
        data = {
            'email': 'test@example.com',
            'consent': False,
            'images': [{'type': 'image/jpeg', 'size': 1000}]
        }
        response = client.post(
            '/api/user/submit',
            json=data,
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_get_status_not_found(self, client):
        """Non-existent submission should return 404."""
        response = client.get('/api/user/status/99999')
        assert response.status_code == 404

    def test_get_status_returns_submission(self, client, sample_submission_data):
        """Should return submission status after creation."""
        # First create a submission
        create_response = client.post(
            '/api/user/submit',
            json=sample_submission_data,
            content_type='application/json'
        )
        submission_id = create_response.get_json()['submission_id']

        # Then get status
        response = client.get(f'/api/user/status/{submission_id}')
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert result['submission_id'] == submission_id
        assert result['status'] in ['pending', 'processing', 'completed', 'failed']
