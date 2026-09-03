import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_company_api_exposes_dynamic_plan_features(api_client, company_a, company_b):
    url = reverse('api:companies_list')
    response = api_client.get(url)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Verifica se a empresa Premium possui as features habilitadas
    comp_a_data = next(c for c in data if c['slug'] == 'lava-jato-a')
    assert comp_a_data['plan_code'] == 'premium'
    assert comp_a_data['features']['has_loyalty'] is True
    assert comp_a_data['features']['has_inspections'] is True

    # Verifica se a empresa Básica possui as features restritas
    comp_b_data = next(c for c in data if c['slug'] == 'lava-jato-b')
    assert comp_b_data['plan_code'] == 'basic'
    assert comp_b_data['features']['has_loyalty'] is False
    assert comp_b_data['features']['has_inspections'] is False
