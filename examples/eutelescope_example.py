'''Example script to run a full analysis on telescope data. The original data can be found in the example folder of the EuTelescope framework.
The telescope consists of 6 planes with 15 cm clearance between the planes. The residual for the second plane (DUT 1) is about 8 um and comparable
to the residuals from EuTelescope software (6 um).

The Mimosa26 has an active area of 21.2mm x 10.6mm and the pixel matrix consists of 1152 columns and 576 rows (18.4um x 18.4um pixel size).
The total size of the chip is 21.5mm x 13.7mm x 0.036mm (radiation length 9.3660734)

The matrix is divided into 4 areas. For each area the threshold can be set up individually.
The quartes are from column 0-287, 288,575, 576-863 and 864-1151.

The Mimosa26 detects ionizing particle with a density of up to 10^6 hits / cm^2 / s. The hit rate for a beam telescope is ~5 hits / frame.
'''

import os
import logging
from multiprocessing import Pool

from testbeam_analysis import hit_analysis
from testbeam_analysis import geometry_utils
from testbeam_analysis import dut_alignment
from testbeam_analysis import track_analysis
from testbeam_analysis import result_analysis
from testbeam_analysis import plot_utils

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - [%(levelname)-8s] (%(threadName)-10s) %(message)s")


if __name__ == '__main__':  # main entry point is needed for multiprocessing under windows
    # The location of the data files, one file per DUT
    data_files = [('data/TestBeamData_Mimosa26_DUT' + str(i) + '.h5') for i in range(6)]  # The first device is the reference for the coordinate system

    # Pixel dimesions and matrix size of the DUTs
    pixel_size = [(18.4, 18.4)] * 6  # Column, row pixel pitch in um
    n_pixel = [(1152, 576)] * 6  # Number of pixel on column, row

    z_positions = [0., 15000, 30000, 45000, 60000, 75000]  # z position in um, can be also deduced from data, but usually not with high precision (~ mm)
    dut_names = ("Tel_0", "Tel_1", "Tel_2", "Tel_3", "Tel_4", "Tel_5")

    output_folder = os.path.split(data_files[0])[0]  # define a folder where all output data and plots are stored

    # The following shows a complete test beam analysis by calling the seperate function in correct order

# FIMXE: this is not ok
# Create the initial geometry (to be done once)
# geo_file = os.path.join(output_folder, 'MimosaGeometry.h5')
#     geometry_utils.create_initial_geometry(geo_file, z_positions)
#     geometry_utils.update_rotation_angle(geo_file, 0, -0.00104)
#     geometry_utils.update_rotation_angle(geo_file, 1, 0.00104)
#     geometry_utils.update_rotation_angle(geo_file, 2, 0.00102)
#     geometry_utils.update_translation_val(geo_file, 1, -10.7, 19.4)
#     geometry_utils.update_translation_val(geo_file, 2, -12.1, 17.4)

    # Remove hot pixel, only needed for devices wih noisy pixel like Mimosa 26
    kwargs = [{
        'input_hits_file': data_files[i],
        'n_pixel': n_pixel[i],
        'pixel_size': pixel_size[i],
        'dut_name': dut_names[i]} for i in range(0, len(data_files))]
    pool = Pool()
    multiple_results = [pool.apply_async(hit_analysis.remove_noisy_pixels, kwds=kwarg) for kwarg in kwargs]
    noisy_pixels_files = [res.get() for res in multiple_results]

    # Cluster hits off all DUTs
    kwargs = [{
        'input_hits_file': noisy_pixels_files[i],
        'max_x_distance': 3,
        'max_y_distance': 3,
        'max_time_distance': 2,
        'max_cluster_hits': 1000000,
        'dut_name': dut_names[i]} for i in range(0, len(data_files))]
    multiple_results = [pool.apply_async(hit_analysis.cluster_hits, kwds=kwarg) for kwarg in kwargs]
    # free resources
    pool.close()
    pool.join()
    noisy_pixels_cluster_files = [res.get() for res in multiple_results]

    # Correlate the row / column of each DUT
    dut_alignment.correlate_hits(input_hits_files=noisy_pixels_files,
                                 output_correlation_file=os.path.join(output_folder, 'Correlation.h5'), fraction=1)
    plot_utils.plot_correlations(input_correlation_file=os.path.join(output_folder, 'Correlation.h5'),
                                 output_pdf=os.path.join(output_folder, 'Correlations.pdf'))

    # Create alignment data for the DUT positions to the first DUT from the correlation data
    # When needed, set offset and error cut for each DUT as list of tuples
    dut_alignment.coarse_alignment(input_correlation_file=os.path.join(output_folder, 'Correlation.h5'),
                                   output_alignment_file=os.path.join(output_folder, 'Alignment.h5'),
                                   output_pdf=os.path.join(output_folder, 'Alignment.pdf'),
                                   pixel_size=pixel_size)

    # Correct all DUT hits via alignment information and merge the cluster tables to one tracklets table aligned at the event number
    dut_alignment.merge_cluster_data(input_cluster_files=noisy_pixels_cluster_files,
                                     input_alignment_file=os.path.join(output_folder, 'Alignment.h5'),
                                     output_tracklets_file=os.path.join(output_folder, 'Tracklets.h5'),
                                     pixel_size=pixel_size)

    # Find tracks from the tracklets and stores the with quality indicator into track candidates table
    track_analysis.find_tracks(input_tracklets_file=os.path.join(output_folder, 'Tracklets.h5'),
                               input_alignment_file=os.path.join(output_folder, 'Alignment.h5'),
                               output_track_candidates_file=os.path.join(output_folder, 'TrackCandidates.h5'))

    # Fit the track candidates and create new track table
    track_analysis.fit_tracks(input_track_candidates_file=os.path.join(output_folder, 'TrackCandidates.h5'),
                              output_tracks_file=os.path.join(output_folder, 'Tracks.h5'),
                              output_pdf=os.path.join(output_folder, 'Tracks.pdf'),
                              z_positions=z_positions,
                              fit_duts=[1, 2, 3, 4],  # Fit tracks for all DUTs
                              include_duts=[-1, 1],  # Use only the DUT before and after the actual DUT for track fitting / interpolation
                              ignore_duts=None,
                              track_quality=2)

    # Calculate the residuals to check the alignment
    result_analysis.calculate_residuals(input_tracks_file=os.path.join(output_folder, 'Tracks.h5'),
                                        output_pdf=os.path.join(output_folder, 'Residuals.pdf'),
                                        z_positions=z_positions,
                                        use_duts=None,
                                        max_chi2=None)
