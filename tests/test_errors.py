from llm_clip.errors import ClipError, NoUsableContent, ForcedTypeAbsent


def test_subclasses_are_cliperror():
    assert issubclass(NoUsableContent, ClipError)
    assert issubclass(ForcedTypeAbsent, ClipError)


def test_message_roundtrips():
    assert str(NoUsableContent("nothing usable")) == "nothing usable"
