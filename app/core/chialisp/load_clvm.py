import functools

from chia.wallet.puzzles.load_clvm import load_clvm

load_clvm_locally = functools.partial(load_clvm, package_or_requirement=__name__)
