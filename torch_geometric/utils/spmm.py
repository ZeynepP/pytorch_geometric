import logging

import torch
from torch import Tensor

import torch_geometric.typing
from torch_geometric.typing import Adj, SparseTensor, torch_sparse
from torch_geometric.utils import is_torch_sparse_tensor


@torch.jit._overload
def spmm(src, other, reduce):
    # type: (Tensor, Tensor, str) -> Tensor
    pass


@torch.jit._overload
def spmm(src, other, reduce):
    # type: (SparseTensor, Tensor, str) -> Tensor
    pass


def spmm(src: Adj, other: Tensor, reduce: str = "sum") -> Tensor:
    """Matrix product of sparse matrix with dense matrix.

    Args:
        src (Tensor or torch_sparse.SparseTensor]): The input sparse matrix,
            either a :class:`torch_sparse.SparseTensor` or a
            :class:`torch.sparse.Tensor`.
        other (Tensor): The input dense matrix.
        reduce (str, optional): The reduce operation to use
            (:obj:`"sum"`, :obj:`"mean"`, :obj:`"min"`, :obj:`"max"`).
            (default: :obj:`"sum"`)

    :rtype: :class:`Tensor`
    """
    reduce = 'sum' if reduce == 'add' else reduce

    if reduce not in ['sum', 'mean', 'min', 'max']:
        raise ValueError(f"`reduce` argument '{reduce}' not supported")

    if isinstance(src, SparseTensor):
        return torch_sparse.matmul(src, other, reduce)

    if not is_torch_sparse_tensor(src):
        raise ValueError("`src` must be a `torch_sparse.SparseTensor` "
                         f"or a `torch.sparse.Tensor` (got {type(src)}).")

    # `torch.sparse.mm` only supports reductions on CPU for PyTorch>=2.0.
    # This will currently throw on error for CUDA tensors.
    if torch_geometric.typing.WITH_PT2:
        if src.layout != torch.sparse_csr:
            logging.warning("Converting sparse tensor to CSR format for more "
                            "efficient processing. Consider converting your "
                            "sparse tensor to CSR format beforehand to avoid "
                            "repeated conversion")
            src = src.to_sparse_csr()
        if reduce == 'sum':
            return torch.sparse.mm(src, other)
        return torch.sparse.mm(src, other, reduce)

    if reduce == 'sum':
        return torch.sparse.mm(src, other)

    # TODO: Support `mean` reduction for PyTorch SparseTensor
    raise ValueError(f"`{reduce}` reduction is not supported for "
                     f"'torch.sparse.Tensor' on device '{src.device}'")
