import numpy as np
from tqdm import tqdm


class KspaceGenerator:
    """
    A Kspace Factory emulate the acquisition of an MRI.

    Parameters
    ----------
    full_kspace: np.ndarray
        The fully sampled kspace, which will be returned incrementally, and a mask, use for the fourier transform
    mask: np.ndarray
        A binary mask, giving the sampled location for the kspace
    """

    def __init__(self, full_kspace: np.ndarray, mask: np.ndarray, max_iter: int = 1):
        self._full_kspace = full_kspace
        self.kspace = full_kspace.copy()
        self.mask = mask
        self._len = max_iter
        self.iter = 0

    @property
    def shape(self):
        return self._full_kspace.shape

    @property
    def dtype(self):
        return self._full_kspace.dtype

    def __len__(self):
        return self._len

    def __iter__(self):
        return self

    def __getitem__(self, idx):
        if idx >= self._len:
            raise IndexError
        else:
             return self._full_kspace, self.mask

    def __next__(self):
        if self.iter < self._len:
            self.iter += 1
            return self._full_kspace, self.mask
        else:
            raise StopIteration

    def reset(self):
        self.iter = 0

    def opt_iterate(self, opt,reset=True):
        if reset:
            self.reset()
        for it, (kspace, mask) in enumerate(tqdm(self)):
            opt.idx += 1
            opt._grad._obs_data = kspace
            opt._grad.fourier_op.mask = mask
            opt._update()
            if opt.metrics and opt.metric_call_period is not None:
                if opt.idx % opt.metric_call_period == 0 or opt.idx == (self._len - 1):
                    opt._compute_metrics()
        opt.retrieve_outputs()

class Column2DKspaceGenerator(KspaceGenerator):
    def __init__(self, full_kspace, mask_cols, max_iter=0):
        mask = np.zeros(full_kspace.shape[1:])

        def flip2center(mask_cols, center_pos):
            """ reorder a list by starting by a center_position and alternating left/right"""
            mask_cols = list(mask_cols)
            left = mask_cols[center_pos::-1]
            right = mask_cols[center_pos + 1:]
            new_cols = []
            while left or right:
                if left:
                    new_cols.append(left.pop(0))
                if right:
                    new_cols.append(right.pop(0))
            return np.array(new_cols)

        self.cols = flip2center(mask_cols, np.argmin(np.abs(mask_cols - full_kspace.shape[2] // 2)))
        if max_iter == 0:
            max_iter = len(self.cols)
        super().__init__(full_kspace, mask, max_iter=max_iter)

    def __getitem__(self, it):
        if it > self._len:
            raise IndexError
        idx = min(it, len(self.cols))
        mask = np.zeros(self.shape[1:])
        mask[:, self.cols[:idx]] = 1
        kspace = self._full_kspace * self.mask[np.newaxis, ...]
        return kspace, mask

    def __next__(self):
        if self.iter > self._len:
            raise StopIteration
        idx = min(self.iter, len(self.cols))
        self.mask[:, self.cols[:idx]] = 1
        self.kspace = self._full_kspace * self.mask[np.newaxis, ...]
        self.iter += 1
        return self.kspace, self.mask
