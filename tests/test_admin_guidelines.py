from app.content.seed import seed_all


async def test_admin_upload_and_link_blueprint_guideline(client, db):
    seeded = await seed_all(db)
    await db.commit()

    created = await client.post("/api/v1/admin/guidelines", json={
        "code": "grammar_rules",
        "version": "v1",
        "role": "evaluation",
        "body_markdown": "# Rules\nCheck the official sample.",
        "frontmatter": {"source": "manual"},
    })
    assert created.status_code == 200, created.text
    guideline = created.json()["data"]
    assert guideline["default_role"] == "evaluation"
    assert guideline["checksum"]

    linked = await client.post(
        f"/api/v1/admin/guidelines/blueprints/{seeded['blueprint'].id}",
        json={
            "guideline_id": guideline["id"],
            "role": "evaluation",
            "position": 1,
            "include_in_generation": False,
            "include_in_evaluation": True,
        },
    )
    assert linked.status_code == 200, linked.text
    assert linked.json()["data"]["code"] == "grammar_rules"

    listed = await client.get(f"/api/v1/admin/guidelines/blueprints/{seeded['blueprint'].id}")
    assert listed.status_code == 200
    assert listed.json()["data"][0]["role"] == "evaluation"
