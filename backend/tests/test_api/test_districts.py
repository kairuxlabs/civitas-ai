from src.models.district import District


async def test_get_districts_empty(client):
    response = await client.get("/api/districts")
    assert response.status_code == 200
    assert response.json() == []


async def test_get_districts(client, db_session):
    db_session.add(District(city_id="hanoi", name="Hoàn Kiếm"))
    await db_session.commit()
    response = await client.get("/api/districts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Hoàn Kiếm"
