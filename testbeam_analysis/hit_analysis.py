''' All functions acting on the hits of one DUT are listed here'''
from __future__ import division

import logging
import os.path
import re

import tables as tb
import numpy as np
from scipy.ndimage import median_filter

from pixel_clusterizer.clusterizer import HitClusterizer
from testbeam_analysis.tools import analysis_utils
from testbeam_analysis.tools.plot_utils import (plot_noisy_pixels,
                                                plot_cluster_size)


def generate_pixel_mask(input_hits_file, n_pixel, pixel_mask_name="NoisyPixelMask", output_mask_file=None, pixel_size=None, threshold=10.0, filter_size=3, dut_name=None, plot=True, chunk_size=1000000):
    '''Generating pixel mask from the hit table.

    The hit table is read in chunks to reduce the memory footprint.

    Parameters
    ----------
    input_hits_file : string
        File name of the hit table.
    n_pixel : tuple
        Tuple of the total number of pixels (column/row).
    pixel_mask_name : string
        Name of the node containing the mask inside the output file.
    output_mask_file : string
        File name of the output mask file.
    pixel_size : tuple
        Tuple of the pixel size (column/row). If None, assuming square pixels.
    threshold : float
        The threshold for pixel masking. The threshold is given in units of
        sigma of the pixel noise (background subtracted). The lower the value
        the more pixels are masked.
    filter_size : scalar or tuple
        Adjust the median filter size by giving the number of columns and rows.
        The higher the value the more the background is smoothed and more
        pixels are masked.
    dut_name : string
        Name of the DUT. If None, file name of the hit table will be printed.
    plot : bool
        If True, create additional output plots.
    chunk_size : int
        Chunk size of the data when reading from file.
    '''
    logging.info('=== Generating %s for %s ===', ' '.join(item.lower() for item in re.findall('[A-Z][^A-Z]*', pixel_mask_name)), input_hits_file)

    if output_mask_file is None:
        output_mask_file = os.path.splitext(input_hits_file)[0] + '_' + '_'.join(item.lower() for item in re.findall('[A-Z][^A-Z]*', pixel_mask_name)) + '.h5'

    occupancy = None
    # Calculating occupancy array
    with tb.open_file(input_hits_file, 'r') as input_file_h5:
        for hits, _ in analysis_utils.data_aligned_at_events(input_file_h5.root.Hits, chunk_size=chunk_size):
            col, row = hits['column'], hits['row']
            chunk_occ = analysis_utils.hist_2d_index(col - 1, row - 1, shape=n_pixel)
            if occupancy is None:
                occupancy = chunk_occ
            else:
                occupancy = occupancy + chunk_occ

    # Run median filter across data, assuming 0 filling past the edges to get expected occupancy
    blurred = median_filter(occupancy.astype(np.int32), size=filter_size, mode='constant', cval=0.0)
    # Spot noisy pixels maxima by substracting expected occupancy
    difference = np.ma.masked_array(occupancy - blurred)
    std = np.ma.std(difference)
    abs_occ_threshold = threshold * std
    occupancy = np.ma.masked_where(difference > abs_occ_threshold, occupancy)
    logging.info('Removed %d hot pixels at threshold %.1f in %s', np.ma.count_masked(occupancy), threshold, input_hits_file)
    # Generate tuple col / row array of hot pixels, do not use getmask()
    noisy_pixels_mask = np.ma.getmaskarray(occupancy)

    with tb.open_file(output_mask_file, 'w') as out_file_h5:
        # Creating occupancy table without masking noisy pixels
        occupancy_array_table = out_file_h5.create_carray(out_file_h5.root, name='HistOcc', title='Occupancy Histogram', atom=tb.Atom.from_dtype(occupancy.dtype), shape=occupancy.shape, filters=tb.Filters(complib='blosc', complevel=5, fletcher32=False))
        occupancy_array_table[:] = np.ma.getdata(occupancy)

        # Creating noisy pixels table
        noisy_pixels_table = out_file_h5.create_carray(out_file_h5.root, name=pixel_mask_name, title='Pixel Mask', atom=tb.Atom.from_dtype(noisy_pixels_mask.dtype), shape=noisy_pixels_mask.shape, filters=tb.Filters(complib='blosc', complevel=5, fletcher32=False))
        noisy_pixels_table[:] = noisy_pixels_mask

    if plot:
        plot_noisy_pixels(input_mask_file=output_mask_file, pixel_size=pixel_size, dut_name=dut_name)

    return output_mask_file


def remove_noisy_pixels(input_hits_file, n_pixel, output_hits_file=None, pixel_size=None, threshold=10.0, filter_size=3, dut_name=None, plot=True, chunk_size=1000000):
    '''Removes noisy pixel from the data file containing the hit table.
    The hit table is read in chunks and for each chunk the noisy pixel are determined and removed.

    To call this function on 8 cores in parallel with chunk_size=1000000 the following RAM is needed:
    11 byte * 8 * 1000000 = 88 Mb

    Parameters
    ----------
    input_hits_file : string
        Input PyTables raw data file.
    n_pixel : tuple
        Tuple of the total number of pixels (column/row).
    pixel_size : tuple
        Tuple of the pixel size (column/row). If None, assuming square pixels.
    threshold : float
        The threshold for pixel masking. The threshold is given in units of sigma of the pixel noise (background subtracted). The lower the value the more pixels are masked.
    filter_size : scalar or tuple
        Adjust the median filter size by giving the number of columns and rows. The higher the value the more the background is smoothed and more pixels are masked.
    dut_name : string
        Name of the DUT. If None, file name of the hit table will be printed.
    plot : bool
        If True, create additional output plots.
    chunk_size : int
        Chunk size of the data when reading from file.
    '''
    logging.info('=== Removing noisy pixel in %s ===', input_hits_file)

    if output_hits_file is None:
        output_hits_file = os.path.splitext(input_hits_file)[0] + '_noisy_pixels.h5'


    output_mask_file = generate_pixel_mask(input_hits_file=input_hits_file, pixel_mask_name="DisabledPixelMask", n_pixel=n_pixel, output_mask_file=None, pixel_size=pixel_size, threshold=threshold, filter_size=filter_size, dut_name=dut_name, plot=plot, chunk_size=chunk_size)

    with tb.open_file(output_mask_file, 'r') as input_file_h5:
        pixel_mask = input_file_h5.root.DisabledPixelMask[:]
        occupancy = input_file_h5.root.HistOcc[:]

    logging.info('Removed %d hot pixels at threshold %.1f in %s', np.count_nonzero(pixel_mask), threshold, input_hits_file)

    # Generate pair of col / row arrays
    masked_pixels = np.nonzero(pixel_mask)
    # Check for any noisy pixels
    if masked_pixels[0].shape[0] != 0:
        # map 2d array (col, row) to 1d array to increase selection speed
        masked_pixels_1d = np.ravel_multi_index(masked_pixels, dims=n_pixel)
    else:
        masked_pixels_1d = []

    # Storing putput files
    with tb.open_file(input_hits_file, 'r') as input_file_h5:
        with tb.open_file(output_hits_file, 'w') as out_file_h5:
            # Creating new hit table without noisy pixels
            hit_table_out = out_file_h5.create_table(out_file_h5.root, name='Hits', description=input_file_h5.root.Hits.dtype, title='Selected not noisy hits for test beam analysis', filters=tb.Filters(complib='blosc', complevel=5, fletcher32=False))
            for hits, _ in analysis_utils.data_aligned_at_events(input_file_h5.root.Hits, chunk_size=chunk_size):
                # Select not noisy pixel
                hits_1d = np.ravel_multi_index((hits['column'] - 1, hits['row'] - 1), dims=n_pixel)
                hits = hits[np.in1d(hits_1d, masked_pixels_1d, invert=True)]
                hit_table_out.append(hits)

            logging.info('Reducing data by a factor of %.2f in file %s', input_file_h5.root.Hits.nrows / hit_table_out.nrows, out_file_h5.filename)

            # Creating occupancy table without masking noisy pixels
            occupancy_array_table = out_file_h5.create_carray(out_file_h5.root, name='HistOcc', title='Occupancy Histogram', atom=tb.Atom.from_dtype(occupancy.dtype), shape=occupancy.shape, filters=tb.Filters(complib='blosc', complevel=5, fletcher32=False))
            occupancy_array_table[:] = occupancy

            # Creating noisy pixels table
            noisy_pixels_table = out_file_h5.create_carray(out_file_h5.root, name='DisabledPixelMask', title='Pixel Mask', atom=tb.Atom.from_dtype(pixel_mask.dtype), shape=pixel_mask.shape, filters=tb.Filters(complib='blosc', complevel=5, fletcher32=False))
            noisy_pixels_table[:] = pixel_mask

    return output_hits_file


def cluster_hits(input_hits_file, output_cluster_file=None, input_disabled_pixel_mask_file=None, input_noisy_pixel_mask_file=None, min_hit_charge=0, max_hit_charge=None, column_cluster_distance=1, row_cluster_distance=1, frame_cluster_distance=1, dut_name=None, plot=True, chunk_size=1000000):
    '''Clusters the hits in the data file containing the hit table.

    Parameters
    ----------
    data_file : pytables file
    output_file : pytables file
    '''

    logging.info('=== Cluster hits in %s ===', input_hits_file)

    if output_cluster_file is None:
        output_cluster_file = os.path.splitext(input_hits_file)[0] + '_cluster.h5'

    if input_disabled_pixel_mask_file is not None:
        with tb.open_file(input_disabled_pixel_mask_file, 'r') as input_file_h5:
             disabled_pixels = np.dstack(np.nonzero(input_file_h5.root.DisabledPixelMask[:]))[0] + 1
    else:
        disabled_pixels = None

    if input_noisy_pixel_mask_file is not None:
        with tb.open_file(input_noisy_pixel_mask_file, 'r') as input_file_h5:
             noisy_pixels = np.dstack(np.nonzero(input_file_h5.root.NoisyPixelMask[:]))[0] + 1
    else:
        noisy_pixels = None

    with tb.open_file(input_hits_file, 'r') as input_file_h5:
        with tb.open_file(output_cluster_file, 'w') as output_file_h5:
            clusterizer = HitClusterizer(column_cluster_distance=column_cluster_distance, row_cluster_distance=row_cluster_distance, frame_cluster_distance=frame_cluster_distance, min_hit_charge=min_hit_charge, max_hit_charge=max_hit_charge)

            # Output data
            cluster_table_description = np.dtype([('event_number', '<i8'),
                                                  ('ID', '<u2'),
                                                  ('n_hits', '<u2'),
                                                  ('charge', 'f4'),
                                                  ('seed_column', '<u2'),
                                                  ('seed_row', '<u2'),
                                                  ('mean_column', 'f4'),
                                                  ('mean_row', 'f4')])
            cluster_table_out = output_file_h5.create_table(output_file_h5.root, name='Cluster', description=cluster_table_description, title='Clustered hits', filters=tb.Filters(complib='blosc', complevel=5, fletcher32=False))

            for hits, _ in analysis_utils.data_aligned_at_events(input_file_h5.root.Hits, chunk_size=chunk_size, try_speedup=False):
                if not np.all(np.diff(hits['event_number']) >= 0):
                    raise RuntimeError('The event number does not always increase. The hits cannot be used like this!')
                cluster_hits, cluster = clusterizer.cluster_hits(hits, noisy_pixels=noisy_pixels, disabled_pixels=disabled_pixels)  # Cluster hits
                if not np.all(np.diff(cluster['event_number']) >= 0):
                    raise RuntimeError('The event number does not always increase. The cluster cannot be used like this!')
                cluster_table_out.append(cluster)

    if plot:
        plot_cluster_size(input_cluster_file=output_cluster_file, dut_name=dut_name)

    return output_cluster_file
