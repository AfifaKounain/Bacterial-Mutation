"""Single-substitution parsing and reference sequence validation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from io import StringIO

from Bio import SeqIO
CANONICAL_AMINO_ACIDS = frozenset("ACDEFGHIKLMNPQRSTVWY")
MUTATION_PATTERN = re.compile(r"^([ACDEFGHIKLMNPQRSTVWY])([1-9][0-9]*)([ACDEFGHIKLMNPQRSTVWY])$")


@dataclass(frozen=True)
class Mutation:
    notation: str
    original: str
    position: int
    mutant: str


@dataclass(frozen=True)
class MutationAnalysis:
    mutation: Mutation
    wild_type_residue: str
    mutant_residue: str
    valid: bool
    message: str


def validate_protein_sequence(sequence: str) -> str:
    normalized = "".join(sequence.split()).upper()
    if not normalized:
        raise ValueError("Enter a non-empty protein sequence.")
    invalid = sorted(set(normalized) - CANONICAL_AMINO_ACIDS)
    if invalid:
        raise ValueError(
            "The sequence contains unsupported amino-acid symbols: "
            + ", ".join(invalid)
            + ". Use the 20 standard amino acids."
        )
    return normalized


def parse_mutation(notation: str) -> Mutation:
    value = notation.strip().upper()
    match = MUTATION_PATTERN.fullmatch(value)
    if not match:
        raise ValueError(
            "Use one substitution in the form A42V. Insertions, deletions, "
            "stop mutations, and multiple mutations are not supported."
        )
    original, raw_position, mutant = match.groups()
    if original == mutant:
        raise ValueError("The original and replacement amino acids must differ.")
    return Mutation(value, original, int(raw_position), mutant)


def parse_fasta(contents: str) -> tuple[str, str]:
    try:
        records = list(SeqIO.parse(StringIO(contents), "fasta"))
    except (ValueError, TypeError) as error:
        raise ValueError(f"Could not read the FASTA file: {error}") from error
    if len(records) != 1:
        raise ValueError("Provide a FASTA file containing exactly one protein sequence.")
    description = records[0].description
    sequence = validate_protein_sequence(str(records[0].seq))
    return description, sequence


def analyze_mutation(sequence: str, notation: str) -> MutationAnalysis:
    protein = validate_protein_sequence(sequence)
    mutation = parse_mutation(notation)
    if mutation.position > len(protein):
        raise ValueError(
            f"Position {mutation.position} is outside the sequence "
            f"(length {len(protein)})."
        )
    residue = protein[mutation.position - 1]
    if residue != mutation.original:
        raise ValueError(
            f"Mutation {mutation.notation} does not match the entered sequence: "
            f"position {mutation.position} contains {residue}, not {mutation.original}."
        )
    return MutationAnalysis(
        mutation=mutation,
        wild_type_residue=residue,
        mutant_residue=mutation.mutant,
        valid=True,
        message="Valid single amino-acid substitution.",
    )


def derive_single_substitution(sequence: str, reference: str) -> str | None:
    """Return notation only when a dataset sequence differs at exactly one site."""
    protein = validate_protein_sequence(sequence)
    reference_sequence = validate_protein_sequence(reference)
    if len(protein) != len(reference_sequence):
        return None
    differences = [
        (index, wild_type, mutant)
        for index, (wild_type, mutant) in enumerate(zip(reference_sequence, protein))
        if wild_type != mutant
    ]
    if len(differences) != 1:
        return None
    index, wild_type, mutant = differences[0]
    return f"{wild_type}{index + 1}{mutant}"


def derive_single_substitution_from_reference_fragment(
    sequence: str,
    reference: str,
) -> tuple[str, int, int] | None:
    """Infer a unique substitution in a contiguous reference-aligned protein fragment.

    The returned inclusive coordinates are 1-based positions in the full reference.
    """
    protein = validate_protein_sequence(sequence)
    reference_sequence = validate_protein_sequence(reference)
    if len(protein) >= len(reference_sequence):
        return None

    matches: list[tuple[str, int, int]] = []
    for start in range(len(reference_sequence) - len(protein) + 1):
        fragment_reference = reference_sequence[start : start + len(protein)]
        differences = [
            (index, wild_type, mutant)
            for index, (wild_type, mutant) in enumerate(zip(fragment_reference, protein))
            if wild_type != mutant
        ]
        if len(differences) == 1:
            index, wild_type, mutant = differences[0]
            matches.append(
                (
                    f"{wild_type}{start + index + 1}{mutant}",
                    start + 1,
                    start + len(protein),
                )
            )
    if len(matches) != 1:
        return None
    return matches[0]
