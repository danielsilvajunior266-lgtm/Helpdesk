import logging
import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from apps.saas_core.models import Plan, Company

User = get_user_model()

@pytest.mark.django_db
def test_security_login_and_logout_logging(caplog):
    caplog.set_level(logging.INFO, logger='apps.security')
    
    plan = Plan.objects.create(name='Pro', code='pro', monthly_price=100)
    company = Company.objects.create(name='Test Wash', plan=plan, status='active')
    user = User.objects.create_user(
        username='sec_test_user',
        email='sec_test@test.com',
        password='ValidPassword123!',
        company=company,
        role='owner'
    )

    client = Client()

    # 1. Test Login Failure Logging
    response = client.post('/auth/login/', {'username': 'sec_test@test.com', 'password': 'WrongPassword!'})
    assert any("LOGIN_FAILURE" in record.message for record in caplog.records)

    # 2. Test Login Success Logging
    caplog.clear()
    response = client.post('/auth/login/', {'username': 'sec_test@test.com', 'password': 'ValidPassword123!'})
    assert any("LOGIN_SUCCESS" in record.message and "sec_test_user" in record.message for record in caplog.records)

    # 3. Test Logout Logging
    caplog.clear()
    client.get('/auth/logout/')
    assert any("LOGOUT" in record.message for record in caplog.records)
