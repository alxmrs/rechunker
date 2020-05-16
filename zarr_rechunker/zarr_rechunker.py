"""Main module."""


import math
from math import prod
from functools import reduce

import numpy as np # type: ignore

from typing import Callable, Iterable, Sequence, Union, Optional, List, Tuple


def consolidate_chunks(shape: Sequence[int],
                       chunks: Sequence[int],
                       itemsize: int,
                       max_mem: int,
                       axes: Optional[Sequence[int]]=None,
                       chunk_limits: Optional[Sequence[int]]=None) -> Sequence[int]:
    """
    Consolidate input chunks up to a certain memory limit. Consolidation starts on the
    highest axis and proceeds towards axis 0.

    Parameters
    ----------
    shape : Tuple
        Array shape
    chunks : Tuple
        Original chunk shape (must be in form (5, 10, 20), no irregular chunks)
    max_mem : Int
        Maximum permissible chunk memory size, measured in units of itemsize
    axes : Iterable, optional
        List of axes on which to consolidate. Otherwise all.
    chunk_limits : Tuple, optional
        Maximum size of each chunk along each axis.

    Returns
    -------
    new_chunks : tuple
        The new chunks, size guaranteed to be <= mam_mem
    """

    if axes is None:
        axes = list(range(len(shape)))
    if chunk_limits is None:
        chunk_limits = shape

    if any([chunk_limits[n_ax] < chunks[n_ax] for n_ax in axes]):
        raise ValueError(f"chunk_limits {chunk_limits} are smaller than chunks {chunks}")

    chunk_mem = itemsize * prod(chunks)
    if chunk_mem > max_mem:
        raise ValueError(f"chunk_mem {chunk_mem} > max_mem {max_mem}")
    headroom = max_mem // chunk_mem

    new_chunks = list(chunks)

    for n_axis in sorted(axes)[::-1]:

        c_new= min(chunks[n_axis] * headroom, shape[n_axis], chunk_limits[n_axis])
        print(f'  axis {n_axis}, {chunks[n_axis]} -> {c_new}')
        new_chunks[n_axis] = c_new
        chunk_mem = itemsize * prod(new_chunks)
        headroom = max_mem // chunk_mem

        if headroom == 1:
            break

    return tuple(new_chunks)


# WIP
def intermediate_chunks(source_shape: Sequence[int],
                          source_chunks: Sequence[int],
                          target_shape: Sequence[int],
                          target_chunks: Sequence[int],
                          itemsize: int,
                          max_mem: int) -> Tuple[Sequence[int]]:
    source_chunk_mem = itemsize * prod(source_chunks)
    target_chunk_mem = itemsize * prod(target_chunks)
    assert source_chunk_mem <= max_mem
    assert target_chunk_mem <= max_mem
    assert target_shape == source_shape
    ndim = len(source_shape)
    assert len(source_chunks) == ndim
    assert len(target_chunks) == ndim

    # Greatest common demoninator chunks.
    # These are the smallest possible chunks which evenly fit into
    # both the source and target.
    # Example:
    #   source_chunks: (20, 5)
    #   target_chunks: (4, 25)
    #.  gcd_chunks:    (4, 5)
    # We don't need to check their memory usage: they are guaranteed to be smaller
    # than both source and target chunks.
    gcd_chunks = [math.gcd(c_source, c_target) for
                  c_source, c_target in zip(source_chunks, target_chunks)]

    # Now consolidate input and output chunks.
    # We read from many chunks at once and write to many chunks at once.
    # But we can't have overlapping writes!
    consolidate_source_axes = [] # type: List(int)
    consolidate_target_axes = [] # type: List(int)
    for n_ax in range(ndim):
        # many intermediate chunks to each target chunk
        # can consolidate reads
        if gcd_chunks[n_ax] < target_chunks[n_ax]:
            consolidate_source_axes.append(n_ax)

    read_chunks = consolidate_chunks(source_shape, source_chunks, itemsize,
                                     max_mem, axes=consolidate_source_axes,
                                     chunk_limits=target_chunks)

    return (gcd_chunks,)
        # input checks
