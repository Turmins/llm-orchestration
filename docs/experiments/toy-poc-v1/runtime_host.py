"""Pinned bundled host readiness, stdio only; no model, account or tool calls."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess

CLI_SHA = '34549ded6e2aee87c911c62d025e52e26c488683d0f489cd68f756baef1a6df6'
HOST_SHA = '850eca242991c4271d1b0fd42e096423efac0046e984f9d2124319dae181a945'
CAPS = ['session-cell-execution-resource-limits', 'yield-observation']


def decode_ready(data):
    if len(data) < 4:
        raise ValueError('host_handshake_truncated')
    size = struct.unpack('<I', data[:4])[0]
    if size > 65536 or size != len(data) - 4:
        raise ValueError('host_handshake_frame_invalid')
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('host_handshake_duplicate_key')
            result[key] = value
        return result
    hello = json.loads(data[4:].decode('utf-8'), object_pairs_hook=pairs)
    if (type(hello) is not dict or set(hello) != {'type', 'selectedVersion', 'capabilities'}
        or hello['type'] != 'connection/ready' or type(hello['selectedVersion']) is not int
        or hello['selectedVersion'] != 1 or type(hello['capabilities']) is not list
        or any(type(c) is not str for c in hello['capabilities'])
        or len(set(hello['capabilities'])) != len(hello['capabilities'])
        or not set(CAPS) <= set(hello['capabilities'])):
        raise ValueError('host_handshake_rejected')
    return dict(protocol_version=1, required_capabilities=CAPS)


def probe(exe):
    found = shutil.which(str(exe))
    if not found:
        raise ValueError('native_codex_exe_required')
    cli = Path(found).resolve()
    # Supported scope is this inspected desktop bundle. No guessed PATH host.
    host = cli.with_name('codex-code-mode-host.exe')
    if hashlib.sha256(cli.read_bytes()).hexdigest() != CLI_SHA:
        raise ValueError('cli_executable_mismatch')
    if not host.is_file() or hashlib.sha256(host.read_bytes()).hexdigest() != HOST_SHA:
        raise ValueError('host_executable_mismatch')
    # Refuse alternate packaged resources; InstallContext prefers them to sibling.
    if (cli.parent / 'codex-resources').exists() or cli.parent.name.lower() in ('bin', 'codex-resources'):
        raise ValueError('host_resolution_unverified')
    hello = dict(type='connection/hello', supportedVersions=[1],
                 requiredCapabilities=[], optionalCapabilities=CAPS)
    body = json.dumps(hello, separators=(',', ':')).encode('utf-8')
    frame = struct.pack('<I', len(body)) + body
    # No args => upstream default stdio. No sockets, sessions or JS execution.
    proc = subprocess.Popen([str(host)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=False,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    try:
        out, err = proc.communicate(frame, timeout=15)
    except BaseException:
        if proc.poll() is None:
            proc.kill()  # This probe's own child only.
        proc.communicate()
        raise ValueError('host_handshake_interrupted') from None
    if proc.returncode != 0 or err.strip():
        raise ValueError('host_handshake_process_failed')
    result = decode_ready(out)
    return dict(host_sha256=HOST_SHA, host_resolution='pinned_bundle_sibling',
                host_availability='stdio_handshake_verified', **result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex', required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(dict(status='passed', inference_launches=0, **probe(args.codex))))
    except (ValueError, OSError) as error:
        print(json.dumps(dict(status='blocked', reason=str(error) if isinstance(error, ValueError)
                              else 'host_filesystem_error', inference_launches=0)))
        raise SystemExit(2)
