"""Tests for expanded lore graph integrity."""

from hypersim.game.story.lore_expanded import (
    ALL_LORE,
    get_lore_by_dimension,
    get_related_lore,
    get_unresolved_related_entries,
)


def test_related_entries_are_resolved():
    """Every related entry ID should map to a real lore entry."""
    assert get_unresolved_related_entries() == {}


def test_get_related_lore_returns_known_links():
    """Related lookup should return linked lore entries in order."""
    related = get_related_lore("tessera_prologue")
    assert [entry.id for entry in related] == [
        "the_first_point",
        "the_first_extension",
        "the_first_unfolding",
    ]


def test_dimension_filter_includes_all_dimension_entries():
    """Dimension queries should include shared 'all' entries."""
    all_dimension_entries = {entry.id for entry in ALL_LORE.values() if entry.dimension == "all"}
    selected = {entry.id for entry in get_lore_by_dimension("2d")}
    assert all_dimension_entries.issubset(selected)
