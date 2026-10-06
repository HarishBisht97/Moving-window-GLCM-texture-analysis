"""Command-line entry point.

Example:
    python src/main.py --image data/aerial_sample.png --window 7 --levels 8 --k 4
"""

import argparse

import matplotlib

matplotlib.use("Agg")

import pandas as pd  # noqa: E402

import config  # noqa: E402
from pipeline import run_experiment  # noqa: E402
from preprocess import load_image  # noqa: E402


def parse_args():
    p = argparse.ArgumentParser(description="Moving-window GLCM texture analysis + K-Means")
    p.add_argument("--image", default=str(config.DEFAULT_IMAGE), help="input image path")
    p.add_argument("--window", type=int, default=config.GLCM_WINDOW_SIZE, help="GLCM window size")
    p.add_argument("--levels", type=int, default=config.GRAY_LEVELS, help="number of gray levels")
    p.add_argument("--distance", type=int, default=config.DISTANCE, help="GLCM pixel distance")
    p.add_argument("--angle", type=int, default=config.ANGLE, choices=[0, 45, 90, 135])
    p.add_argument("--k", type=int, default=config.NUM_CLUSTERS, help="number of K-Means clusters")
    p.add_argument("--smooth", type=int, nargs="+", default=config.SMOOTHING_SIZES,
                   help="averaging filter sizes")
    p.add_argument("--symmetric", action="store_true", help="use a symmetric GLCM")
    p.add_argument("--out", default=str(config.OUTPUT_DIR), help="output directory")
    return p.parse_args()


def main():
    args = parse_args()
    image = load_image(args.image)
    print(f"Loaded {args.image}: {image.shape[1]}x{image.shape[0]}, "
          f"min {image.min():.1f}, max {image.max():.1f}")
    _, fstats, cstats, metrics, text = run_experiment(
        image, smoothing_sizes=args.smooth, window_size=args.window, num_levels=args.levels,
        distance=args.distance, angle=args.angle, k=args.k, symmetric=args.symmetric,
        output_dir=args.out)
    with pd.option_context("display.width", 160, "display.max_columns", 20,
                           "display.float_format", "{:.4f}".format):
        print("\nTexture feature statistics\n", fstats.to_string(index=False))
        print("\nCluster statistics\n", cstats.to_string(index=False))
        print("\nComparison metrics\n", metrics.to_string(index=False))
    print("\n" + text)


if __name__ == "__main__":
    main()
