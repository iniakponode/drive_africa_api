from tests.db_fixtures import (
    TestingSessionLocal,
    client,
    create_api_client,
    create_tables,
    drop_tables,
)


def setup_database():
    drop_tables()
    create_tables()


def teardown_database():
    drop_tables()


def test_admin_settings_and_config():
    setup_database()
    try:
        with TestingSessionLocal() as db:
            admin_key = create_api_client(db, role="admin")

        headers = {"X-API-Key": admin_key}
        cloud_get = client.get("/api/admin/cloud-endpoints", headers=headers)
        assert cloud_get.status_code == 200

        cloud_put = client.put(
            "/api/admin/cloud-endpoints",
            json={
                "road_limits_url": "https://roads.example.com",
                "driving_tips_url": "https://tips.example.com",
            },
            headers=headers,
        )
        assert cloud_put.status_code == 200
        payload = cloud_put.json()
        assert payload["road_limits_url"] == "https://roads.example.com"

        config_get = client.get("/api/config/cloud-endpoints", headers=headers)
        assert config_get.status_code == 200
        assert config_get.json()["driving_tips_url"] == "https://tips.example.com"

        dataset_get = client.get("/api/admin/dataset-access", headers=headers)
        assert dataset_get.status_code == 200
        assert "behaviour_metrics" in dataset_get.json()["datasets"]

        dataset_put = client.put(
            "/api/admin/dataset-access",
            json={"datasets": {"behaviour_metrics": ["admin"]}},
            headers=headers,
        )
        assert dataset_put.status_code == 200
        assert dataset_put.json()["datasets"]["behaviour_metrics"] == ["admin"]
    finally:
        teardown_database()
