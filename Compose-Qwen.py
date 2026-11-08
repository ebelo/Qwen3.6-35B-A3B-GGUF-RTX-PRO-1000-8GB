"""Compose the exact recorded Qwen artifact from two pinned, local GGUF files.

Python standard library only. No downloads or network access. Existing output is
never overwritten. This handles only the pinned GGUF v3, 32-byte-aligned layout.
"""
import argparse
import hashlib
import pathlib
import shutil
import struct

BASE_SHA = 'ac0e2c1189e055faa36eff361580e79c5bd6f8e76bffb4ce547f167d53e31a61'
MTP_SHA = '0b21525e972670ed59e1812e170b27c26355381f0656ecc4e25617ece7dac58b'
OUTPUT_SHA = 'ad2c4475849c923233dda2269facec79d3b056de08627ea770a3f6ef6592bf54'
OUTPUT_SIZE = 22663387424


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def directory(path):
    with path.open('rb') as stream:
        def scalar(fmt):
            size = struct.calcsize('<' + fmt)
            return struct.unpack('<' + fmt, stream.read(size))[0]

        def string():
            return stream.read(scalar('Q')).decode('utf-8')

        sizes = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 4, 7: 1,
                 10: 8, 11: 8, 12: 8}

        def skip(kind):
            if kind in sizes:
                stream.seek(sizes[kind], 1)
            elif kind == 8:
                stream.seek(scalar('Q'), 1)
            elif kind == 9:
                subtype, count = scalar('I'), scalar('Q')
                if subtype in sizes:
                    stream.seek(count * sizes[subtype], 1)
                else:
                    for _ in range(count):
                        skip(subtype)
            else:
                raise ValueError('Unsupported GGUF metadata type')

        if stream.read(4) != b'GGUF' or scalar('I') != 3:
            raise ValueError('Expected GGUF version 3')
        tensor_count, metadata_count = scalar('Q'), scalar('Q')
        for _ in range(metadata_count):
            string()
            skip(scalar('I'))
        tensors = []
        for _ in range(tensor_count):
            name = string()
            dimensions = tuple(scalar('Q') for _ in range(scalar('I')))
            tensors.append((name, dimensions, scalar('I'), scalar('Q')))
        return (stream.tell() + 31) // 32 * 32, tensors


def compose(base, mtp, output):
    if output.exists():
        raise FileExistsError('Output already exists; choose a new output path')
    for path, expected in [(base, BASE_SHA), (mtp, MTP_SHA)]:
        if digest(path) != expected:
            raise ValueError('Input SHA-256 mismatch: ' + path.name)
    base_start, base_tensors = directory(base)
    mtp_start, mtp_tensors = directory(mtp)
    if len(base_tensors) != 733 or len(mtp_tensors) != 753:
        raise ValueError('Unexpected tensor counts')
    if base_tensors != mtp_tensors[:733]:
        raise ValueError('Base and MTP tensor layouts do not match')
    tail_start = mtp_start + mtp_tensors[733][3]
    if base.stat().st_size - base_start != tail_start - mtp_start:
        raise ValueError('Unexpected base tensor payload length')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as dest, mtp.open('rb') as draft, base.open('rb') as target:
        dest.write(draft.read(mtp_start))
        target.seek(base_start)
        shutil.copyfileobj(target, dest, 8 * 1024 * 1024)
        draft.seek(tail_start)
        shutil.copyfileobj(draft, dest, 8 * 1024 * 1024)
    if output.stat().st_size != OUTPUT_SIZE or digest(output) != OUTPUT_SHA:
        raise ValueError('Output verification failed; do not use the output')
    print('Verified benchmark artifact SHA-256: ' + OUTPUT_SHA)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=pathlib.Path, required=True)
    parser.add_argument('--mtp', type=pathlib.Path, required=True)
    parser.add_argument('--output', type=pathlib.Path, required=True)
    options = parser.parse_args()
    compose(options.base, options.mtp, options.output)
