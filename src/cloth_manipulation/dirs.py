import datetime
import inspect
import json
import os


def save_dict_as_json(path, dict):
    with open(path, "w") as f:
        json.dump(dict, f)


def ensure_output_filepaths(run_dir=None, config=None):
    if run_dir is None:
        caller_filepath = inspect.stack()[1].filename
        caller_dirpath = os.path.dirname(caller_filepath)
        print(caller_filepath)

        experiment_output_dir = os.path.join(caller_dirpath, "output")

        if not os.path.exists(experiment_output_dir):
            os.mkdir(experiment_output_dir)

        if config is None:
            run_dir = os.path.join(experiment_output_dir, str(datetime.datetime.now()))
        else:
            run_dirname = "_".join(["=".join([str(k), str(v)]) for k, v in config.items()])
            run_dir = os.path.join(experiment_output_dir, run_dirname)

            if os.path.exists(run_dir):
                run_dir += f"_time={datetime.datetime.now()}"

        os.mkdir(run_dir)

    print(run_dir)

    paths = {
        "run": run_dir,
        "config": os.path.join(run_dir, "config.json"),
        "losses": os.path.join(run_dir, "losses.json"),
        "blend": os.path.join(run_dir, "results.blend"),
        "video": os.path.join(run_dir, "video.mp4"),
    }

    subdir_names = ["cipc", "renders"]

    for name in subdir_names:
        subdir = os.path.join(run_dir, name)
        os.mkdir(subdir)
        paths[name] = subdir

    return paths
