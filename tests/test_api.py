import io
import os
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    os.environ["GLCM_STORAGE_DIR"] = str(tmp_path_factory.mktemp("storage"))
    from fastapi.testclient import TestClient
    from backend.app import app
    return TestClient(app)


def _png_bytes(arr):
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return buf.getvalue()


def _wait(client, analysis_id, timeout=120):
    deadline = time.time() + timeout
    while time.time() < deadline:
        st = client.get(f"/api/analysis/{analysis_id}/status").json()
        if st["state"] in ("completed", "failed"):
            return st
        time.sleep(0.2)
    raise TimeoutError


def test_upload_rejects_bad_type(client):
    r = client.post("/api/upload", files={"file": ("x.gif", b"GIF89a", "image/gif")})
    assert r.status_code == 400


def test_parameter_validation(client):
    r = client.post("/api/analyze", json={"imageId": "0" * 32, "glcmWindowSize": 6})
    assert r.status_code == 422
    r = client.post("/api/analyze", json={"imageId": "0" * 32, "glcmWindowSize": 3, "distance": 3})
    assert r.status_code == 422


def test_full_analysis_flow(client):
    rng = np.random.default_rng(0)
    img = np.zeros((96, 96), dtype=np.uint8)
    img[:, :48] = 60
    img[:, 48:] = rng.integers(100, 250, (96, 48))
    r = client.post("/api/upload", files={"file": ("test.png", _png_bytes(img), "image/png")})
    assert r.status_code == 200, r.text
    meta = r.json()
    assert meta["width"] == 96 and meta["height"] == 96 and meta["dataType"] == "uint8"
    assert client.get(meta["previewUrl"]).status_code == 200

    r = client.post("/api/analyze", json={"imageId": meta["imageId"], "glcmWindowSize": 7,
                                          "grayLevels": 8, "distance": 1, "angle": 45,
                                          "clusters": 3, "randomState": 1})
    assert r.status_code == 202, r.text
    aid = r.json()["analysisId"]
    st = _wait(client, aid)
    assert st["state"] == "completed", st
    assert all(s["state"] == "done" for s in st["stages"])

    res = client.get(f"/api/analysis/{aid}/results").json()
    assert [e["label"] for e in res["experiments"]] == ["Original", "7x7 smoothed", "9x9 smoothed"]
    exp = res["experiments"][0]
    assert {t["feature"] for t in exp["textures"]} == {"ASM", "CON", "MEAN"}
    assert len(exp["clusters"]) == 3
    assert abs(sum(c["percent"] for c in exp["clusters"]) - 100) < 1e-6
    assert len(res["featureStatistics"]) == 9
    assert res["parameters"]["angle"] == 45 and res["parameters"]["randomState"] == 1

    for url in [exp["inputImageUrl"], exp["kmeansImageUrl"], exp["textures"][0]["imageUrl"],
                res["comparisonGridUrl"]]:
        assert client.get(url).status_code == 200, url
    names = {d["name"] for d in res["downloads"]}
    assert {"feature_statistics.csv", "comparison_grid.png", "smoothed_9x9.png"} <= names

    z = client.get(res["zipUrl"])
    assert z.status_code == 200
    assert "cluster_statistics.csv" in zipfile.ZipFile(io.BytesIO(z.content)).namelist()


def test_file_traversal_blocked(client):
    r = client.get("/api/analysis/" + "a" * 32 + "/files/..%2F..%2Fsettings.py")
    assert r.status_code == 404
    assert client.get("/api/analysis/not-an-id/status").status_code == 404
