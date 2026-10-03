import json

import pytest


CONTRACT = "contracts/citelock.py"
COMMIT = "a" * 40
ARGS = (
    "example-receipt",
    "genlayerlabs",
    "example",
    COMMIT,
    "README.md",
    "The service is available in English and Spanish.",
    "The service supports Spanish.",
)


def test_supported_receipt_and_replay_guard(direct_vm, direct_deploy):
    direct_vm.mock_web(
        r"raw\.githubusercontent\.com/genlayerlabs/example/",
        {"status": 200, "body": "The service is available in English and Spanish."},
    )
    direct_vm.mock_llm(r"Classify whether the exact source quote", '{"decision":"SUPPORTED"}')
    contract = direct_deploy(CONTRACT)

    contract.attest(*ARGS)
    receipt = json.loads(contract.get_receipt("example-receipt"))
    assert receipt["decision"] == "SUPPORTED"
    assert receipt["source_url"].endswith(f"/{COMMIT}/README.md")
    assert len(receipt["source_sha256"]) == 64

    with direct_vm.expect_revert("receipt_id already used"):
        contract.attest(*ARGS)


def test_missing_quote_does_not_call_llm(direct_vm, direct_deploy):
    direct_vm.mock_web(
        r"raw\.githubusercontent\.com/genlayerlabs/example/",
        {"status": 200, "body": "A different document."},
    )
    contract = direct_deploy(CONTRACT)
    contract.attest(*ARGS)
    receipt = json.loads(contract.get_receipt("example-receipt"))
    assert receipt["decision"] == "QUOTE_MISSING"


@pytest.mark.parametrize("invalid", ["short", "g" * 40, "../README.md"])
def test_invalid_source_inputs_revert_before_web(direct_vm, direct_deploy, invalid):
    contract = direct_deploy(CONTRACT)
    args = list(ARGS)
    if invalid == "../README.md":
        args[4] = invalid
    else:
        args[3] = invalid
    with direct_vm.expect_revert():
        contract.attest(*args)
    assert contract.get_receipt("example-receipt") == ""


def test_validator_independently_classifies(direct_vm, direct_deploy):
    direct_vm.mock_web(
        r"raw\.githubusercontent\.com/genlayerlabs/example/",
        {"status": 200, "body": "The service is available in English and Spanish."},
    )
    direct_vm.mock_llm(r"Classify whether the exact source quote", '{"decision":"SUPPORTED"}')
    contract = direct_deploy(CONTRACT)
    contract.attest(*ARGS)

    direct_vm.clear_mocks()
    direct_vm.mock_web(
        r"raw\.githubusercontent\.com/genlayerlabs/example/",
        {"status": 200, "body": "The service is available in English and Spanish."},
    )
    direct_vm.mock_llm(r"Classify whether the exact source quote", '{"decision":"UNCLEAR"}')
    assert direct_vm.run_validator() is False
