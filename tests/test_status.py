from io import StringIO
from pathlib import Path
from unittest.mock import mock_open, patch

from softioc.builder import ClearRecords, records


def test_builder_create_status_pv(status_gen):
    p = "BL01T-MO-MOTOR-01"
    inpa = "BL01T-MO-MOTOR-01:MOTOR1.MOVN"
    status_gen.create_status_pv(prefix=p, inputs=[inpa])

    status_pv = """
record(calc, "BL01T-MO-MOTOR-01:STA")
{
    field(ACKT, "NO")
    field(CALC, "(A|B|C|D|E|F|G|H|I|J|K|L)>0?1:0")
    field(INPA, "BL01T-MO-MOTOR-01:MOTOR1.MOVN")
    field(INPB, "")
    field(INPC, "")
    field(INPD, "")
    field(INPE, "")
    field(INPF, "")
    field(INPG, "")
    field(INPH, "")
    field(INPI, "")
    field(INPJ, "")
    field(INPK, "")
    field(INPL, "")
    field(SCAN, "1 second")
}
"""

    assert status_gen.status_pvs != {}

    # Fake file-like object to "print" the record to
    auto_status_pv = StringIO()
    # Get the string representation of the record
    status_gen.status_pvs[p].Print(auto_status_pv)

    assert auto_status_pv.getvalue() == status_pv

    # Make sure the record is deleted
    ClearRecords()


def test_builder_write_status_pvs(status_gen):
    # To mock the open() function used in _write_status_pvs
    m = mock_open()

    p = "BL01T-MO-MOTOR-01"
    inpa = "BL01T-MO-MOTOR-01:MOTOR1.MOVN"
    status_pv = records.calc(  # pyright: ignore[reportAttributeAccessIssue]
        f"{p}:STA",
        CALC="(A|B|C|D|E|F|G|H|I|J|K|L)>0?1:0",
        SCAN="1 second",
        ACKT="NO",
        INPA=inpa,
    )
    status_gen.status_pvs[p] = status_pv

    # Mock the Print() function so we don't actually write a file
    with (
        patch("builtins.open", m),
        patch("techui_builder.builder.Record.Print") as mock_print,
    ):
        status_gen.write_status_pvs()

        # Check open() was called with the correct args
        m.assert_called_once_with(
            Path(status_gen._write_directory.joinpath("config/status.db")),
            "w",
        )
        mock_print.assert_called_once()

    # Make sure the record is deleted
    ClearRecords()
