from feedbackapi.schemas import FeedbackCreate

async def test_create_feedback(client):
    data = FeedbackCreate(title="Test Feedback", content="This is a test")
    response = await client.post("/feedback", json=data.dict())
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["title"] == data.title
    assert json_data["content"] == data.content
    assert "id" in json_data

async def test_list_feedback(client):
    # Create a feedback first
    data = FeedbackCreate(title="Another Test", content="Another content")
    await client.post("/feedback", json=data.dict())

    # List all feedbacks
    response = await client.get("/feedback")
    assert response.status_code == 200
    feedbacks = response.json()
    assert isinstance(feedbacks, list)
    assert any(f["title"] == data.title for f in feedbacks)
