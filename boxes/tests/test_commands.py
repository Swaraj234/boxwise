import pytest
from django.core.management import call_command

from boxes.models import Box, Order, Product


@pytest.mark.django_db
def test_seed_demo_data_command():
    call_command("seed_demo_data", clear=True)

    assert Product.objects.count() == 7
    assert Box.objects.count() == 5
    assert Order.objects.count() == 2

    # Re-run without clear to test update_or_create paths
    call_command("seed_demo_data")
    assert Product.objects.count() == 7
    assert Box.objects.count() == 5
    assert Order.objects.count() == 2
