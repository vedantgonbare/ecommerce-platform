import pytest
import pytest_asyncio
import uuid


@pytest_asyncio.fixture
async def category_chain(client):
    """Creates a 3-level category chain: root -> middle -> leaf. Returns all three ids."""
    root_response = await client.post("/categories/", json={
        "name": f"Root {uuid.uuid4().hex[:8]}"
    })
    root_id = root_response.json()["id"]

    middle_response = await client.post("/categories/", json={
        "name": f"Middle {uuid.uuid4().hex[:8]}", "parent_id": root_id
    })
    middle_id = middle_response.json()["id"]

    leaf_response = await client.post("/categories/", json={
        "name": f"Leaf {uuid.uuid4().hex[:8]}", "parent_id": middle_id
    })
    leaf_id = leaf_response.json()["id"]

    return {"root_id": root_id, "middle_id": middle_id, "leaf_id": leaf_id}

@pytest.mark.asyncio
async def test_update_category_direct_self_parent_rejected(client, category_chain):
    root_id = category_chain["root_id"]

    response = await client.put(f"/categories/{root_id}", json={"parent_id": root_id})
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_update_category_creates_cycle_rejected(client, category_chain):
    root_id = category_chain["root_id"]
    leaf_id = category_chain["leaf_id"]

    # attempt to make root's parent be leaf — leaf's chain already passes through root
    response = await client.put(f"/categories/{root_id}", json={"parent_id": leaf_id})
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_update_category_valid_reparent_succeeds(client, category_chain):
    leaf_id = category_chain["leaf_id"]

    # create a brand-new, unrelated category to reparent leaf under
    new_parent_response = await client.post("/categories/", json={
        "name": f"Unrelated {uuid.uuid4().hex[:8]}"
    })
    new_parent_id = new_parent_response.json()["id"]

    response = await client.put(f"/categories/{leaf_id}", json={"parent_id": new_parent_id})
    assert response.status_code == 200
    assert response.json()["parent_id"] == new_parent_id

@pytest.mark.asyncio
async def test_update_category_nonexistent_parent_rejected(client, category_chain):
    root_id = category_chain["root_id"]
    fake_parent_id = "00000000-0000-0000-0000-000000000000"

    response = await client.put(f"/categories/{root_id}", json={"parent_id": fake_parent_id})
    assert response.status_code == 400