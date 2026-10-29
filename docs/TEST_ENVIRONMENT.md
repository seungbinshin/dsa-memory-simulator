# Offline JavaScript verification environment

The resumed strict provenance check passed, but the final read-only acceptance sandbox
caught a separate test setup problem: Node tried to open a system OpenSSL configuration
before running the generated-JavaScript syntax and display-value tests. That path was
outside the sandbox's permitted reads. This was a startup dependency failure; neither
JavaScript test had executed. The failing sensor result is retained in the audit history.

The tests now share a small `run_node` helper that uses Node's documented
`--openssl-config` option with Python's platform-specific `os.devnull`. These checks
parse offline JavaScript or execute a small DOM sink with fixture values. They use no
network, TLS or cryptographic behavior. The change is confined to these test subprocesses;
it does not alter the simulator, generated dashboard, system configuration or sandbox.
No denied file was copied, read through another path, or newly authorized.

All original assertions remain. Nonzero startup or JavaScript exit codes still fail;
no error is caught and converted into success or a skip. The existing optional checks
still skip only when Node itself is absent. A new regression creates a malformed
OpenSSL config in an allowed temporary directory, supplies it as `OPENSSL_CONF`, and
requires the helper to execute JavaScript and return exactly `42`. Before the helper
was isolated, this test failed at OpenSSL parsing; after the fix it must pass.
The suite now contains 45 tests, including this extra regression.

The separate provenance regression also verified that a simulated 107ns metadata
mismatch is rejected while the real file's SHA256, size and nanosecond timestamp remain
unchanged. That owner check does not modify actual file times or weaken the validator.

This report and the test-only repair have fresh pre-write observations in an authorized
HexaHarness continuation with inherited counters. Publication still requires current
build/syntax/test results, strict runtime/artifact verification and the same managed
acceptance sensors. Earlier validation counts in dated reports describe the earlier
44-test version; output and screenshot hashes remain unchanged.

A subsequent independent read found this report's modification time had changed by
58 nanoseconds after completion, while its bytes and size still matched. The strict
acceptance sensor rejected that completion too. The failed records remain intact.
Both host and sandbox then observed the same current file metadata. The responsible
writer or synchronization layer has not been identified; floating-point precision
remains a reproduced possibility, not an established cause. This additional observation
is recorded through a normal authorized continuation. The saved report is separately
read before new completion evidence is captured, and the same exact metadata check
must pass again. No file-time setter, manual record correction or tolerance is used.
