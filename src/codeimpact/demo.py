"""Small, deterministic checkout-service example with a meaningful change."""

from codeimpact.models import AnalysisRequest, Snapshot


def demo_request() -> AnalysisRequest:
    files = {
        "shop/pricing.py": ("def discount(total):\n    return total * 0.10\n"),
        "shop/cart.py": (
            "from shop.pricing import discount\n"
            "\n"
            "def checkout(total):\n"
            "    return total - discount(total)\n"
        ),
        "shop/api.py": (
            "from shop.cart import checkout\n"
            "\n"
            "def create_order(total):\n"
            '    return {"total": checkout(total)}\n'
        ),
        "shop/health.py": ('def health():\n    return "ok"\n'),
        "tests/test_pricing.py": (
            "from shop.pricing import discount\n"
            "\n"
            "def test_discount():\n"
            "    assert discount(100) == 10\n"
        ),
        "tests/test_cart.py": (
            "from shop.cart import checkout\n"
            "\n"
            "def test_checkout():\n"
            "    assert checkout(100) == 90\n"
        ),
        "tests/test_api.py": (
            "from shop.api import create_order\n"
            "\n"
            "def test_create_order():\n"
            '    assert create_order(100)["total"] == 90\n'
        ),
        "tests/test_health.py": (
            'from shop.health import health\n\ndef test_health():\n    assert health() == "ok"\n'
        ),
    }
    head = files | {"shop/pricing.py": "def discount(total):\n    return total * 0.15\n"}
    return AnalysisRequest(
        base=Snapshot(files=files),
        head=Snapshot(files=head),
        label="Checkout service · discount 10% → 15%",
    )
