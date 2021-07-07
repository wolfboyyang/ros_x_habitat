import argparse
import csv
import habitat
from habitat.config import Config
from habitat.config.default import get_config
from src.classes.habitat_evaluator import HabitatEvaluator
import os

# logging
from src.classes import utils_logging


def main():
    # parse input arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-type",
        default="blind",
        choices=["blind", "rgb", "depth", "rgbd"],
    )
    parser.add_argument("--model-path", default="", type=str)
    parser.add_argument(
        "--task-config", type=str, default="configs/pointnav_d_orignal.yaml"
    )
    parser.add_argument("--episode-id", type=str, default="-1")
    parser.add_argument(
        "--scene-id",
        type=str,
        default="data/scene_datasets/habitat-test-scenes/skokloster-castle.glb",
    )
    parser.add_argument(
        "--seed-file-path", type=str, default="seed=7.csv"
    )
    parser.add_argument("--log-dir", type=str, default="logs/")
    args = parser.parse_args()

    # get exp config
    exp_config = get_config(args.task_config)

    # get seeds if provided; otherwise use default seed from Habitat
    seeds = []
    if args.seed_file_path != "":
        with open(args.seed_file_path, newline='') as csv_file:
            csv_lines = csv.reader(csv_file)
            for line in csv_lines:
                seeds.append(int(line[0]))
    else:
        seeds = [exp_config.SEED]
    
    # create log dir
    try:
        os.mkdir(f"{args.log_dir}")
    except FileExistsError:
        pass

    # create logger and log experiment settings
    logger = utils_logging.setup_logger(__name__, f"{args.log_dir}/summary-all_seeds.log")
    logger.info("Experiment configuration:")
    logger.info(exp_config)

    # instantiate a discrete/continuous evaluator
    evaluator = None
    if "PHYSICS_SIMULATOR" in exp_config:
        logger.info("Instantiating continuous simulator with dynamics")
        evaluator = HabitatEvaluator(config_paths=args.task_config, input_type=args.input_type, model_path=args.model_path, enable_physics=True)
    elif "SIMULATOR" in exp_config:
        logger.info("Instantiating discrete simulator")
        evaluator = HabitatEvaluator(config_paths=args.task_config, input_type=args.input_type, model_path=args.model_path, enable_physics=False)
    else:
        logger.info("Simulator not properly specified")
        raise NotImplementedError

    logger.info("Started Evaluation")
    for seed in seeds:
        # create logger for each seed and log the seed
        logger_per_seed = utils_logging.setup_logger(f"{__name__}-seed={seed}",
        f"{args.log_dir}/summary-seed={seed}.log"
        )
        logger_per_seed.info(f"Seed = {seed}")

        # create (per-episode) log dir
        try:
            os.mkdir(f"{args.log_dir}/seed={seed}")
        except FileExistsError:
            pass

        # evaluate
        metrics = evaluator.evaluate(
            episode_id_last=args.episode_id,
            scene_id_last=args.scene_id,
            log_dir=f"{args.log_dir}/seed={seed}",
            agent_seed=seed
        )

        # log metrics
        logger_per_seed.info("Printing average metrics:")
        for k, v in metrics.items():
            logger_per_seed.info("{}: {:.3f}".format(k, v))
        utils_logging.close_logger(logger_per_seed)

    utils_logging.close_logger(logger)


if __name__ == "__main__":
    main()
