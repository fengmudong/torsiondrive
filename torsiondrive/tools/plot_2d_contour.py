#!/usr/bin/env python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def load_data_from_scan_xyz(filename):
    """ Read the dihedral information and energy from scan.xyz """
    with open(filename) as f:
        lines = f.readlines()
    n_atoms = int(lines[0])
    comment_lines = lines[1::n_atoms+2]
    grid_data = dict()
    for line in comment_lines:
        ls = line.strip().split()
        assert ls[0] == 'Dihedral' and ls[-2] == 'Energy', line
        grid_energy = float(ls[-1])
        grid_coord = []
        for i in range(1, len(ls) - 2):
            c = int(ls[i].replace('(', '').replace(',','').replace(')',''))
            grid_coord.append(c)
        grid_data[tuple(grid_coord)] = grid_energy
    return grid_data

def find_grid_spacing(grid_id_list):
    """ Find the largest possible grid spacing for one dimension grid id list """
    if not grid_id_list: return None
    assert all(-180 < grid_id <= 180 for grid_id in grid_id_list), f"grid id out of range (-180, 180]: {grid_id_list}"
    if len(grid_id_list) == 1:
        # find the largest possible grid spacing if only one data is available this direction
        # The answer is the largest divisor of
        # a: grid range 360
        # b: distance from grid_id to -180
        grid_id = grid_id_list[0]
        res = largest_common_divisor(360, grid_id+180)
    else:
        n = len(grid_id_list)
        grid_id_list = sorted(grid_id_list)
        res = 360
        for i in range(n):
            gid = grid_id_list[i]
            spacing = largest_common_divisor(360, gid+180)
            res = largest_common_divisor(res, spacing)
            if i < n-1:
                step = grid_id_list[i+1] - gid
                res = largest_common_divisor(res, step)
    return res

def largest_common_divisor(a, b):
    """ Get the largest common divisor of a and b """
    while b:
        a, b = b, a%b
    return a

def format_2d_grid_data(grid_data, verbose=False):
    """ Take a grid_data dictionary, figure out the grid spacing of each dimension,
    then return the formatted x_array, y_array and z_mat

    Parameters
    ----------
    grid_data: Dict
        {gid: energy} generated by load_data_from_scan_xyz()

    Returns
    -------
    x_array: numpy.ndarray of shape (n_grid1,)
        All possible values for the first dihedral angle in the 2d scan
    y_array: numpy.ndarray of shape (n_grid2,)
        All possible values for the second dihedral angle in the 2d scan
    z_mat: numpy.ndarray of shape (n_grid1, n_grid2)
        The energies of the 2-D scan. Missing points have values np.nan
    """
    if not grid_data:
        raise ValueError("Empty grid data")
    # determine 2d grid dimensions
    sorted_grid_ids = sorted(grid_data)
    assert len(sorted_grid_ids[0]) == 2, 'Only 2-D scan result is supported'
    # find the smallest difference in each dimension to be the spacing
    grid_id_list_1 = sorted(set(grid_id[0] for grid_id in sorted_grid_ids))
    grid_id_list_2 = sorted(set(grid_id[1] for grid_id in sorted_grid_ids))
    grid_spacing_1 = find_grid_spacing(grid_id_list_1)
    grid_spacing_2 = find_grid_spacing(grid_id_list_2)
    grid_size_1 = int(360 / grid_spacing_1)
    grid_size_2 = int(360 / grid_spacing_2)
    if verbose:
        print(f"grid_spacing: [{grid_spacing_1}, {grid_spacing_2}]")
        print(f"grid_size:    [{grid_size_1}, {grid_size_2}]")
    # create data matrix
    x_array = np.arange(-180, 180, grid_spacing_1, dtype=int) + grid_spacing_1
    y_array = np.arange(-180, 180, grid_spacing_2, dtype=int) + grid_spacing_2
    z_mat = np.zeros((grid_size_1, grid_size_2))
    for i, x in enumerate(x_array):
        for j, y in enumerate(y_array):
            z_mat[i, j] = grid_data.get((x,y), np.nan)
    return x_array, y_array, z_mat

def plot_grid_contour(grid_data, pdf_filename, method='imshow', vmax=None):
    """ Plot grid data as a contour map """
    if not grid_data:
        print("Empty grid data, returning")
        return
    x_array, y_array, z_mat = format_2d_grid_data(grid_data)
    # convert abs energies to relative energies
    z_mat = (z_mat - np.nanmin(z_mat)) * 627.509
    # plot
    plt.Figure()
    if method == 'imshow':
        plt.imshow(z_mat, vmax=vmax, cmap='rainbow', origin='lower', extent=(-165, 180, -165, 180))
    elif method == 'contourf':
        plt.contourf(y_array, x_array, z_mat, vmax=vmax, antialiased=True, cmap='rainbow')
    plt.colorbar()
    plt.xticks(x_array[1::2], x_array[1::2])
    plt.yticks(y_array[1::2], y_array[1::2])
    cs = plt.contour(y_array, x_array, z_mat, vmax=vmax, antialiased=True, colors='black')
    plt.clabel(cs, fontsize=9, inline=1)
    plt.savefig(pdf_filename)
    plt.close()

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help='scan.xyz file from torsionscan launch')
    parser.add_argument("-m", "--method", choices=['contourf', 'imshow'], default='imshow', help='method to color background')
    parser.add_argument("--vmax", type=float, help='max value of heat map')
    args = parser.parse_args()

    grid_data = load_data_from_scan_xyz(args.infile)
    pdf_filename = "contour.pdf"
    plot_grid_contour(grid_data, pdf_filename, method=args.method, vmax=args.vmax)
    print("Plot saved as contour.pdf")

if __name__ == '__main__':
    main()
