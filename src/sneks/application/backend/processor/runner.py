import datetime
import hashlib
import json
import operator
import os
import pathlib
import shutil
import struct
import typing
from collections import namedtuple

import boto3

from sneks.application.engine.config.config import config
from sneks.application.engine.engine import runner

if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3ServiceResource
    from mypy_boto3_s3.service_resource import Bucket, BucketObjectsCollection
else:
    S3ServiceResource = object
    Bucket = object
    BucketObjectsCollection = object


Score = namedtuple("Score", ["name", "age", "ended", "age1", "ended1"])

working_dir_root = "/tmp"
registrar_prefix = f"{working_dir_root}/submitted"
record_prefix = f"{working_dir_root}/output"


def run(submission_bucket_name: str) -> tuple[list[dict], list[Score]]:
    config.registrar_prefix = registrar_prefix
    shutil.rmtree(registrar_prefix, ignore_errors=True)

    get_snake_submissions(bucket_name=submission_bucket_name)
    videos: list[dict] = []
    scores: list[Score] = run_scoring()
    return videos, scores


def record(
    submission_bucket_name: str, video_bucket_name: str
) -> tuple[list[str], list[Score]]:
    config.registrar_prefix = registrar_prefix
    shutil.rmtree(registrar_prefix, ignore_errors=True)
    shutil.rmtree(record_prefix, ignore_errors=True)

    get_snake_submissions(bucket_name=submission_bucket_name)
    run_recordings()
    videos: list[str] = encode_videos(video_bucket_name)
    scores: list[Score] = []
    return videos, scores


def get_snake_submissions(bucket_name: str):
    # s3 list objects prefix
    s3: S3ServiceResource = boto3.resource("s3")
    bucket: Bucket = s3.Bucket(bucket_name)
    objects: BucketObjectsCollection = bucket.objects.filter(Prefix="submitted/")

    # sort by user_id, timestamp, desc
    keys = [obj.key for obj in objects]
    keys.sort(reverse=True)
    paths = [pathlib.PurePosixPath(key) for key in keys]

    # get latest (user_id, timestamp) tuple for each user
    user_latest: dict[str, str] = {}
    for path in paths:
        user_latest.setdefault(path.parts[1], path.parts[2])

    # remove non-latest paths
    filtered_paths = [
        path for path in paths if path.parts[2] == user_latest.get(path.parts[1])
    ]

    for filtered_path in filtered_paths:
        filename = f"{working_dir_root}/{filtered_path}"
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        bucket.download_file(str(filtered_path), filename)


def run_recordings() -> None:
    assert config.graphics is not None
    config.runs = 1
    config.graphics.display = True
    config.graphics.headless = True
    config.graphics.record = True
    config.graphics.record_prefix = record_prefix

    runner.main()


def run_scoring() -> list[Score]:
    config.runs = 1
    if config.graphics is not None:
        config.graphics.display = False
    normalized_scores = runner.main()
    assert normalized_scores is not None
    scores = [
        Score(
            name=s.raw.name,
            age=s.raw.age,
            ended=s.raw.ended,
            age1=s.age,
            ended1=s.ended,
        )
        for s in normalized_scores
    ]

    return aggregate_scores(scores)


def aggregate_scores(scores: list[Score]) -> list[Score]:
    # Aggregate both raw values and normalized
    aggregation: dict[str, Score] = dict()
    counts: dict[str, int] = dict()

    for score in scores:
        if score.name in aggregation:
            aggregation[score.name] = Score._make(
                map(operator.add, score, aggregation[score.name])
            )._replace(name=score.name)
        else:
            aggregation[score.name] = score
        counts[score.name] = counts.get(score.name, 0) + 1
    for name in aggregation:
        score = aggregation[name]
        count = counts[name]
        aggregation[name] = Score(
            name=name,
            age=score.age / count,
            ended=score.ended / count,
            age1=score.age1 / count,
            ended1=score.ended1 / count,
        )

    return list(aggregation.values())


def encode_videos(video_bucket_name) -> list[str]:
    s3: S3ServiceResource = boto3.resource("s3")
    bucket: Bucket = s3.Bucket(video_bucket_name)
    prefix = pathlib.Path(f"{record_prefix}/movies/")
    videos = list(prefix.glob("*.mp4"))
    results = []
    for video in videos:
        print(video)
        name = f"{datetime.datetime.utcnow().timestamp()}_{video.relative_to(prefix)}"
        results.append(name)
        with open(video, "rb") as f:
            bucket.upload_fileobj(f, f"games/{name}")
    return results


def save_manifest(
    video_names: list[str],
    scores: list[Score],
    distribution_id: str,
    static_site_bucket_name: str,
) -> None:
    assert config.graphics is not None
    names = sorted([score.name for score in scores])
    color_index_delta = max(len(config.graphics.colors.snake) // len(names), 1)
    colors = [
        config.graphics.colors.snake[i % len(config.graphics.colors.snake)]
        for i in range(0, color_index_delta * len(names), color_index_delta)
    ]
    color_map = {
        name: dict(body=color, head=get_head_color(color))
        for name, color in zip(names, colors)
    }

    timestamp = datetime.datetime.utcnow().isoformat(timespec="seconds")
    structure = {
        "videos": [f"https://www.sneks.dev/games/{video}" for video in video_names],
        "scores": [
            score._asdict()
            for score in sorted(scores, key=lambda s: s.age1 + s.ended1, reverse=True)
        ],
        "colors": color_map,
        "timestamp": timestamp,
    }
    print(structure)
    s3: S3ServiceResource = boto3.resource("s3")
    bucket: Bucket = s3.Bucket(static_site_bucket_name)

    try:
        manifest = json.loads(
            bucket.Object("games/manifest.json").get()["Body"].read().decode("utf-8")
        )
        bucket.Object(f"games/manifest_{manifest['timestamp']}.json").copy(
            CopySource=dict(Bucket=static_site_bucket_name, Key="games/manifest.json")
        )
    except:
        # ignore no manifest
        pass

    bucket.put_object(
        Body=json.dumps(structure).encode("utf-8"), Key="games/manifest.json"
    )


def get_head_color(color: tuple[int, int, int]) -> tuple[int, int, int]:
    return struct.unpack("BBB", hashlib.md5(struct.pack("BBB", *color)).digest()[-3:])
