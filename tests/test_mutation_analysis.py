import pytest

from src.mutation_analysis import (
    analyze_mutation,
    parse_fasta,
    parse_mutation,
    validate_protein_sequence,
)
from src.reference import REFERENCE_SEQUENCE


def test_parses_valid_single_substitution():
    mutation = parse_mutation("m1c")
    assert (mutation.original, mutation.position, mutation.mutant) == ("M", 1, "C")


@pytest.mark.parametrize("notation", ["A0V", "A42", "A42V-G", "A42*", "A42A", "A42V;C2D"])
def test_rejects_unsupported_or_invalid_mutation_notation(notation):
    with pytest.raises(ValueError):
        parse_mutation(notation)


def test_checks_reference_residue_and_position():
    result = analyze_mutation(REFERENCE_SEQUENCE, "M1C")
    assert result.valid
    assert result.wild_type_residue == "M"
    assert result.mutant_residue == "C"
    with pytest.raises(ValueError, match="contains"):
        analyze_mutation(REFERENCE_SEQUENCE, "A1C")
    with pytest.raises(ValueError, match="outside"):
        analyze_mutation(REFERENCE_SEQUENCE, "A999V")


def test_validates_sequence_and_fasta():
    assert validate_protein_sequence(" acd\n") == "ACD"
    with pytest.raises(ValueError, match="non-empty"):
        validate_protein_sequence(" \n ")
    with pytest.raises(ValueError, match="unsupported"):
        validate_protein_sequence("ACDX")
    description, sequence = parse_fasta(">test protein\nM\n")
    assert description == "test protein"
    assert sequence == "M"
    with pytest.raises(ValueError, match="exactly one"):
        parse_fasta(">one\nA\n>two\nC\n")
