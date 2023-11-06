from __future__ import annotations

from blspy import PrivateKey
from chia.wallet.derive_keys import _derive_path_unhardened


def master_sk_to_root_sk(master: PrivateKey) -> PrivateKey:
    return _derive_path_unhardened(master, [12381, 8444, 2050])


def root_sk_to_gateway_sk(root: PrivateKey) -> PrivateKey:
    return _derive_path_unhardened(root, [0])
