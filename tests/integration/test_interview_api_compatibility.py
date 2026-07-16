from backend.models.schemas import InterviewStatusResponse, StartInterviewResponse


def test_start_response_keeps_public_fields():
    schema = StartInterviewResponse.model_json_schema()

    assert set(schema["properties"]) == {
        "thread_id",
        "resume_text",
        "target_position",
        "question",
        "round",
        "resume_file_url",
    }


def test_submit_response_keeps_public_fields():
    schema = InterviewStatusResponse.model_json_schema()

    assert set(schema["properties"]) == {
        "thread_id",
        "is_finished",
        "question",
        "report",
        "round",
    }
