# CiteLock

CiteLock records a source SHA-256 and a consensus decision for a pinned GitHub file.

An attestation points to a specific Git commit and file, not a mutable branch. The caller supplies an exact quote from that file and a short claim. The contract fetches the file from `raw.githubusercontent.com`, checks whether the quote exists, asks an LLM to classify the claim using only the quote, and stores an immutable receipt. A validator independently fetches the source and classifies the claim, then compares its source hash and decision with the leader's result.

This is an experiment in source-bound AI consensus, not a guarantee that a claim is true. `SUPPORTED` means the quoted text directly supports the claim under the validators' shared classification; `CONTRADICTED` means it directly contradicts it; `UNCLEAR` covers ambiguity; and `QUOTE_MISSING` means the exact quote was absent. A receipt records the source hash so later readers can detect source changes or retrieval differences.

## Contract

Source: [`contracts/citelock.py`](contracts/citelock.py)

- `attest(receipt_id, owner, repository, commit, path, quote, claim)` writes one receipt. `commit` must be a full 40-character SHA-1 Git commit ID. The source is capped at 64 KiB; quote and claim lengths are bounded.
- `get_receipt(receipt_id)` returns the receipt as JSON, or an empty string if it does not exist.
- Receipt IDs cannot be reused. The state stores a map from ID to the source URL, SHA-256, quote, claim, decision, and caller address.
- The source URL is constructed from validated GitHub path components; callers cannot supply an arbitrary network host.
- The validator runs the source fetch and classification independently. A mismatch rejects the leader's nondeterministic result.

## Deployment

GenLayer Studio network, chain ID `61999`. Deployed with the Rabby address `0x1942a9F07648b899C4d253897682d6Dc587448A1` on 2026-10-04.

- [Contract](https://explorer-studio.genlayer.com/address/0x3877Df245aEf03c0eCb92646FbBa3Fb59b67486D)
- [Deployment transaction](https://explorer-studio.genlayer.com/tx/0xc8080248e7addfaa192e2c71edf5e6fc493647cfa38704cc04960875cace61f9)

Studio's deployment status was **ACCEPTED**. This is the Studio network; the address is not presented as a mainnet deployment.

An [attestation transaction](https://explorer-studio.genlayer.com/tx/0xf1aae44d2b9d432fde1a110278f80a5ee24dfc0c31a769d67418f50e9a56ab7e) reached **ACCEPTED** consensus. `get_receipt("readme-self-attestation-1")` returned `SUPPORTED` for this README's first sentence at commit `6bab872d8749b5734d682ab57f9f4f72cc92be60`, with source SHA-256 `4375de099e02c74fd7a9e927e39f2dc5180b9bf314127e3862735592f4e1be89`.

## Try it

Open the contract in Studio and call `attest` with a real pinned commit, an exact quote from a UTF-8 file, and a claim about that quote. Use `get_receipt` with the same ID after the transaction is accepted. This README's first sentence can be used as a quote once you substitute this repository's actual 40-character commit ID.

## Development checks

The source passed Python compilation and `genvm-lint lint` (three AST checks). The direct-test suite is in [`tests/test_citelock.py`](tests/test_citelock.py). At the initial publication, `gltest` could not run because its latest GenVM release points to a missing `genvm-universal.tar.xz` asset. This is an environment tooling issue, not evidence that the tests passed. The Studio deployment and subsequent transaction checks are reported separately.

## Limits

GitHub availability, validator web access, and LLM classification can make a transaction fail or disagree. Pinning a commit and recording a hash make the evidence reproducible, but the contract does not authenticate the repository owner or prove that the source's statements are factual. Exact byte-for-byte quote matching is intentional; formatting differences may produce `QUOTE_MISSING`.
