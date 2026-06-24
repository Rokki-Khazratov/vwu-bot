"""Admin catalog CRUD (Phase 2 finish)."""


async def test_create_and_update_subject(client):
    created = await client.post("/api/v1/admin/subjects", json={
        "code": "german", "name": "German", "description": "DE prep",
    })
    assert created.status_code == 200, created.text
    subject_id = created.json()["data"]["id"]

    # appears in public catalog
    listing = await client.get("/api/v1/subjects")
    assert "german" in [s["code"] for s in listing.json()["data"]]

    upd = await client.patch(f"/api/v1/admin/subjects/{subject_id}", json={"name": "German B2"})
    assert upd.json()["data"]["name"] == "German B2"

    logs = await client.get("/api/v1/admin/audit-logs?entity_type=subject")
    actions = [x["action"] for x in logs.json()["data"]]
    assert "subject_create" in actions and "subject_update" in actions


async def test_build_exam_hierarchy(client):
    await client.post("/api/v1/admin/subjects", json={"code": "math", "name": "Mathematics"})
    exam = await client.post("/api/v1/admin/exam-profiles", json={
        "subject_code": "math", "code": "vwu_math", "name": "VWU Math", "level": "b1",
    })
    assert exam.status_code == 200, exam.text
    skill = await client.post("/api/v1/admin/skills", json={
        "exam_profile_code": "vwu_math", "code": "algebra", "name": "Algebra",
    })
    skill_id = skill.json()["data"]["id"]
    fam = await client.post("/api/v1/admin/task-families", json={
        "skill_id": skill_id, "code": "numeric_problem", "name": "Numeric Problem",
        "answer_format": "numeric",
    })
    assert fam.status_code == 200, fam.text

    # hierarchy is browsable through the public catalog
    skills = await client.get("/api/v1/exam-profiles/vwu_math/skills")
    assert [s["code"] for s in skills.json()["data"]] == ["algebra"]
    fams = await client.get(f"/api/v1/skills/{skill_id}/task-families")
    assert [f["code"] for f in fams.json()["data"]] == ["numeric_problem"]


async def test_deactivate_subject_hides_from_catalog(client):
    created = await client.post(
        "/api/v1/admin/subjects", json={"code": "chem", "name": "Chemistry"}
    )
    sid = created.json()["data"]["id"]
    await client.patch(f"/api/v1/admin/subjects/{sid}", json={"is_active": False})
    listing = await client.get("/api/v1/subjects")
    assert "chem" not in [s["code"] for s in listing.json()["data"]]
