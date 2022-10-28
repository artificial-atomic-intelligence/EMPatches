# -*- coding: utf-8 -*-
"""
Created on Mon Mar  7 15:32:58 2022

@author: talha
"""

import numpy as np
import math



class EMPatches(object):
    
    def __init__(self):
        pass

    def extract_patches(self, img, patchsize, overlap=None, stride=None):
        '''
        Parameters
        ----------
        img : image to extract patches from in [H W Ch] format.
        patchsize :  size of patch to extract from image only square patches can be
                     extracted for now.
        overlap (Optional): overlap between patched in percentage a float between [0, 1].
        stride (Optional): Step size between patches
        Returns
        -------
        img_patches : a list containing extracted patches of images.
        indices : a list containing indices of patches in order, whihc can be used 
                  at later stage for 'merging_patches'.
    
        '''

        height = img.shape[0]
        width = img.shape[1]
        maxWindowSize = patchsize
        windowSizeX = maxWindowSize
        windowSizeY = maxWindowSize
        windowSizeX = min(windowSizeX, width)
        windowSizeY = min(windowSizeY, height)

        if stride is not None:
            stepSizeX = stride
            stepSizeY = stride
        elif overlap is not None:
            overlapPercent = overlap

            windowSizeX = maxWindowSize
            windowSizeY = maxWindowSize
            # If the input data is smaller than the specified window size,
            # clip the window size to the input size on both dimensions
            windowSizeX = min(windowSizeX, width)
            windowSizeY = min(windowSizeY, height)

            # Compute the window overlap and step size
            windowOverlapX = int(math.floor(windowSizeX * overlapPercent))
            windowOverlapY = int(math.floor(windowSizeY * overlapPercent))

            stepSizeX = windowSizeX - windowOverlapX
            stepSizeY = windowSizeY - windowOverlapY
        else:
            stepSizeX = 1
            stepSizeY = 1
        
        # Determine how many windows we will need in order to cover the input data
        lastX = width - windowSizeX
        lastY = height - windowSizeY
        xOffsets = list(range(0, lastX+1, stepSizeX))
        yOffsets = list(range(0, lastY+1, stepSizeY))
        
        # Unless the input data dimensions are exact multiples of the step size,
        # we will need one additional row and column of windows to get 100% coverage
        if len(xOffsets) == 0 or xOffsets[-1] != lastX:
        	xOffsets.append(lastX)
        if len(yOffsets) == 0 or yOffsets[-1] != lastY:
        	yOffsets.append(lastY)
        
        img_patches = []
        indices = []
        
        for xOffset in xOffsets:
            for yOffset in yOffsets:
              if len(img.shape) >= 3:
                  img_patches.append(img[(slice(yOffset, yOffset+windowSizeY, None),
                                          slice(xOffset, xOffset+windowSizeX, None))])
              else:
                  img_patches.append(img[(slice(yOffset, yOffset+windowSizeY),
                                          slice(xOffset, xOffset+windowSizeX))])
                  
              indices.append((yOffset, yOffset+windowSizeY, xOffset, xOffset+windowSizeX))
        
        return img_patches, indices
    
    
    def merge_patches(self, img_patches, indices, mode='overwrite'):
        '''
        Parameters
        ----------
        img_patches : list containing image patches that needs to be joined, dtype=uint8
        indices : a list of indices generated by 'extract_patches' function of the format;
                    (yOffset, yOffset+windowSizeY, xOffset, xOffset+windowSizeX)
        mode : how to deal with overlapping patches;
                overwrite -> next patch will overwrite the overlapping area of the previous patch.
                max -> maximum value of overlapping area at each pixel will be written.
                min -> minimum value of overlapping area at each pixel will be written.
                avg -> mean/average value of overlapping area at each pixel will be written.
        Returns
        -------
        Stitched image.
        '''
        modes = ["overwrite", "max", "min", "avg"]
        if mode not in modes:
            raise ValueError(f"mode has to be either one of {modes}, but got {mode}")

        orig_h = indices[-1][1]
        orig_w = indices[-1][3]
        
        rgb = True
        if len(img_patches[0].shape) == 2:
            rgb = False
        
        if mode == 'min':
            if rgb:
                empty_image = np.zeros((orig_h, orig_w, 3)).astype(np.float32) + np.inf # using float here is better
            else:
                empty_image = np.zeros((orig_h, orig_w)).astype(np.float32) + np.inf # using float here is better
        else:
            if rgb:
                empty_image = np.zeros((orig_h, orig_w, 3)).astype(np.float32)# using float here is better
            else:
                empty_image = np.zeros((orig_h, orig_w)).astype(np.float32)# using float here is better


        for i, indice in enumerate(indices):
            if mode == 'overwrite':
                if rgb:
                    empty_image[indice[0]:indice[1], indice[2]:indice[3], :] = img_patches[i]
                else:
                    empty_image[indice[0]:indice[1], indice[2]:indice[3]] = img_patches[i]
            elif mode == 'max':
                if rgb:
                    empty_image[indice[0]:indice[1], indice[2]:indice[3], :] = np.maximum(img_patches[i], empty_image[indice[0]:indice[1], indice[2]:indice[3], :])
                else:
                    empty_image[indice[0]:indice[1], indice[2]:indice[3]] = np.maximum(img_patches[i], empty_image[indice[0]:indice[1], indice[2]:indice[3]])
            elif mode == 'min':
                if rgb:
                    empty_image[indice[0]:indice[1], indice[2]:indice[3], :] = np.minimum(img_patches[i], empty_image[indice[0]:indice[1], indice[2]:indice[3], :])
                else:
                    empty_image[indice[0]:indice[1], indice[2]:indice[3]] = np.minimum(img_patches[i], empty_image[indice[0]:indice[1], indice[2]:indice[3]])
            elif mode == 'avg':
                if rgb:
                    empty_image[indice[0]:indice[1], indice[2]:indice[3], :] = np.where(empty_image[indice[0]:indice[1], indice[2]:indice[3], :] == 0,
                                                                                        img_patches[i], 
                                                                                        np.add(img_patches[i],empty_image[indice[0]:indice[1], indice[2]:indice[3], :])/2)
                    # Below line should work with np.ones mask but giving Weights sum to zero error and is approx. 10 times slower then np.where
                    # empty_image[indice[0]:indice[1], indice[2]:indice[3], :] = np.average(([empty_image[indice[0]:indice[1], indice[2]:indice[3], :],
                    #                                                                         img_patches[i]]), axis=0,
                    #                                                                         weights=(np.asarray([empty_image[indice[0]:indice[1], indice[2]:indice[3], :],
                    #                                                                                               img_patches[i]])>0))
                else:
                    empty_image[indice[0]:indice[1], indice[2]:indice[3]] = np.where(empty_image[indice[0]:indice[1], indice[2]:indice[3]] == 0,
                                                                                    img_patches[i], 
                                                                                    np.add(img_patches[i],empty_image[indice[0]:indice[1], indice[2]:indice[3]])/2)

        return empty_image


class BatchPatching(EMPatches):
    def __init__(self, patchsize, overlap=None, stride=None, typ='tf'):
        '''
        Parameters
        ----------
        patchsize :  size of patch to extract from image only square patches can be
                     extracted for now.
        overlap (Optional): overlap between patched in percentage a float between [0, 1].
        stride (Optional): Step size between patches
        type: Type of batched images tf or torch type
        '''
        super().__init__()
        self.patchsize = patchsize
        self.overlap = overlap
        self.stride = stride
        self.typ = typ

    def patch_batch(self, batch):
        '''
        Parameters
        ----------
        batch : Batch of images of shape either BxCxHxW -> pytorch or BxHxWxC -> tf
                to extract patches from in list(list1, list2, ...),
                where, list1->([H W C], [H W C], ...) and so on.

        Returns
        -------
        batch_patches : a list containing lists of extracted patches of images.
        batch_indices : a list containing lists of indices of patches in order, whihc can be used 
                  at later stage for 'merging_patches'.
    
        '''
        typs = ["tf", "torch"]
        if self.typ not in typs:
            raise ValueError(f"mode has to be either one of {typs}, but got {self.typ}")
        if len(batch.shape) < 4:
            raise ValueError(f'Input batch should be of shape BxCxHxW or BxHxWxC i.e. 4 dims, but got {len(batch.shape)} dims')
        
        if self.typ == 'torch':
            batch = batch.transpose(0,2,3,1)
        
        img_list = list(batch)

        b_patches, b_indices = [], []
        for i in range(len(img_list)):
            patches, indices = super().extract_patches(img_list[i], self.patchsize, self.overlap, self.stride)
            b_patches.append(patches)
            b_indices.append(indices)
        
        return b_patches, b_indices

    def merge_batch(self, b_patches, b_indices, mode='overwrite'):
        '''
        Parameters
        ----------
        b_patches : list containing lists of patches of images to be merged together
                    e.g. list(list1, list2, ...), where, list1->([H W C], [H W C], ...) and so on.
        b_indices : list containing lists of indices of images to be merged in format as return by
                    patch_batch method.

        Returns
        -------
        merged_batch : a np array of shape BxCxHxW -> pytorch or BxHxWxC -> tf.
        
        '''
        m_patches = []
        for p, i in zip(b_patches, b_indices):
            m = super().merge_patches(p, i, mode)
            m_patches.append(m)

        m_patches = np.asarray(m_patches)
        
        if self.typ == 'torch':
            m_patches = m_patches.transpose(0,3,2,1)

        return m_patches
        

def patch_via_indices(img, indices):
    '''
        Parameters
        ----------
        img : image of shape HxWxC or HxW.
        indices :   list of indices/tuple of 4 e.g;
                    [(ystart, yend, xstart, xend), -> indices of 1st patch
                     (ystart, yend, xstart, xend), -> indices of 2nd patch
                     ...]
        Returns
        -------
        img_patches : a list containing extracted patches of image.
        '''
    img_patches=[]
    
    for indice in indices:
        if len(img.shape) >= 3:
            img_patches.append(img[(slice(indice[0], indice[1], None),
                                    slice(indice[2], indice[3], None))])
        else:
            img_patches.append(img[(slice(indice[0], indice[1]),
                                    slice(indice[2], indice[3]))])
