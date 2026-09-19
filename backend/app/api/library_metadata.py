def library_metadata(row):
    return {
        "library_question_id": getattr(row, "library_question_id", None),
        "library_revision": getattr(row, "library_revision", None),
        "library_title": getattr(row, "library_title", None),
    }
