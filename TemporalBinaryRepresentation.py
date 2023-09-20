import numpy as np
from time import time
import torch

class TemporalBinaryRepresentation:
    """
    @brief: Class for Temporal Binary Representation using N bits
    """

    def __init__(self, N: int, width: int, height: int, incremental: bool=False, cuda: bool=True):
        self.N = N
        self.width = width
        self.height = height
        self._mask = np.ones((self.N, self.height, self.width))
        self.incremental = incremental
        self.cuda = cuda

        # Build the mask
        for i in range(N):
            self._mask[i, :, :] = 2 ** i

        if self.incremental:
            self.frame_stack = torch.zeros((self.N, self.height, self.width))
            self.index = self.N-1
            self.frame = torch.zeros((self.height, self.width))
            if self.cuda:
                self.frame_stack = self.frame_stack.cuda()
                self.frame = self.frame.cuda()

    def encode(self, mat: np.array) -> np.array:
        """
        @brief: Encode events using binary encoding
        @param: mat
        @return: Encoded frame
        """

        frame = np.sum((mat * self._mask), 0) / (2 ** (self.N-1))
        return frame

    def incremental_update(self, mat: np.array) -> np.array:
        """
        @brief: Incrementally updates the frame representation by shifting the N-channel tensor and adding the new Most Significant Bit. MSB is the last channel in self.frame
        """
        assert self.incremental == True
        tt = time()
        mat = torch.tensor(mat)
        if self.cuda:
            mat = mat.cuda()
        
        self.index = (self.index + 1) % self.N
        self.frame -= self.frame_stack[self.index]
        self.frame /= 2
        self.frame_stack /= 2
        self.frame_stack[self.index] = mat
        self.frame += mat

        return self.frame
