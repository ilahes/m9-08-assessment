"""Offline checks for tools, safety validation, and failure handling."""

from agent import calculate, check_warranty, lookup_order


def check(condition: bool, label: str) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        raise AssertionError(label)


def main() -> None:
    order = lookup_order("A1001")
    check(order["ok"] and order["price"] == 1200.0, "known order lookup")

    missing = lookup_order("A9999")
    check(not missing["ok"], "unknown order handled gracefully")

    malformed = lookup_order("../../secret")
    check(not malformed["ok"], "malformed order ID rejected")

    arithmetic = calculate("1200 * 2")
    check(arithmetic == {"ok": True, "result": 2400}, "safe arithmetic works")

    divide_zero = calculate("5 / 0")
    check(not divide_zero["ok"], "division by zero handled gracefully")

    injection = calculate("__import__('os').system('dir')")
    check(not injection["ok"], "code-injection expression rejected")

    attribute_attack = calculate("(1).__class__")
    check(not attribute_attack["ok"], "attribute-access expression rejected")

    warranty = check_warranty("A1001")
    check(warranty["ok"] and "warranty_active" in warranty, "warranty tool works")

    print("\nAll offline checks passed.")


if __name__ == "__main__":
    main()
