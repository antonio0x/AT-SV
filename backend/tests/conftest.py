from decimal import Decimal
import pytest


@pytest.fixture
def decimal_amounts() -> list[Decimal]:
    return [Decimal("100"), Decimal("0"), Decimal("1"), Decimal("0.001")]
