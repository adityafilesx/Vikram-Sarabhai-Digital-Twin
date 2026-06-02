import pytest
from persona.persona_engine import PersonaEngine
from persona.timeline_handler import TimelineHandler

def test_persona_engine_get_era():
    engine = PersonaEngine()
    assert engine.get_era_from_year(1947) == 'early_career'
    assert engine.get_era_from_year(1960) == 'space_era'
    assert engine.get_era_from_year(1969) == 'institution_building'
    assert engine.get_era_from_year(1980) is None

def test_timeline_handler():
    handler = TimelineHandler()
    context = handler.get_era_context(1963)
    assert context is not None
    assert context.era_name == "The Space Era Dawns"
    
    constraint = handler.build_temporal_constraint(1963)
    assert "1963" in constraint
    assert "ISRO (1969)" in constraint # ISRO wasn't formed yet
