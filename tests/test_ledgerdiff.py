import unittest
from textwrap import dedent

from ledgerdiff.ledgerdiff import (
    diff_ledger_text,
)


class TestLedgerDiff(unittest.TestCase):
    def test_empty_diff_on_equal_strings(self):
        self.assertEqual(diff_ledger_text("a\n", "a\n"), "")

    def test_outputs_correctly_formatted_ed_style_diff_1(self):
        original = dedent("""\
            ; aaa
            ; ccc
            ; ddd
            ; 111
            ; eee
            ; fff
            ; GGG
        """)
        new = dedent("""\
            ; 000
            ; 111
            ; aaa
            ; bbb
            ; ccc
            ; ddd
            ; eee
            ; fff
            ; ggg
        """)
        ed_diff = dedent("""\
            0a1,2
            > ; 000
            > ; 111
            1a4
            > ; bbb
            4d6
            < ; 111
            7c9
            < ; GGG
            ---
            > ; ggg
        """).strip()
        self.assertEqual(diff_ledger_text(original, new).strip(), ed_diff)

    def test_outputs_correctly_formatted_ed_style_diff_2(self):
        original = dedent("""\
            ; preamble
            ; orig

            P 2021/04/01 1.00 CHF USD
            P 2021/04/03 1.00 CHF USD
        """)
        new = dedent("""\
            ; preamble
            ; dest

            P 2021/04/02 1.00 CHF USD
        """)
        ed_diff = dedent("""\
            2c2
            < ; orig
            ---
            > ; dest
            4,5c4
            < P 2021/04/01 1.00 CHF USD
            < P 2021/04/03 1.00 CHF USD
            ---
            > P 2021/04/02 1.00 CHF USD
        """).strip()
        self.assertEqual(diff_ledger_text(original, new).strip(), ed_diff)

    def test_uses_empty_lines_as_buffers_nr_1(self):
        original = dedent("""\
            2021-05-09 Coop L
                content CC

            2021-05-14 Coop L
                content CC
        """)
        new = dedent("""\
            2021-05-10 * Coop R
                content BCGE

            2021/05/14 Coop R
                content CC
        """)
        ed_diff = dedent("""\
            1,2c1,2
            < 2021-05-09 Coop L
            <     content CC
            ---
            > 2021-05-10 * Coop R
            >     content BCGE
            4c4
            < 2021-05-14 Coop L
            ---
            > 2021/05/14 Coop R
        """).strip()
        self.assertEqual(diff_ledger_text(original, new).strip(), ed_diff)

    def test_uses_empty_lines_as_buffers_nr_2(self):
        original = dedent("""\
            P 2021/04/01 1.00 CHF USD

            P 2021/04/03 1.00 CHF USD
        """)
        new = dedent("""\
            P 2021/04/01 1.00 CHF USD

            P 2021/04/02 1.00 CHF USD

            P 2021/04/04 1.00 CHF USD
        """)
        ed_diff = dedent("""\
            1a2,3
            > 
            > P 2021/04/02 1.00 CHF USD
            3c5
            < P 2021/04/03 1.00 CHF USD
            ---
            > P 2021/04/04 1.00 CHF USD
        """).strip()
        self.assertEqual(diff_ledger_text(original, new).strip(), ed_diff)

    def test_correctly_diffs_a_file_0(self):
        original = dedent("""\
            2021-04-27 * AMZN Mktp DE, AMAZON.DE
              Assets:Liquid:BCGE CC            CHF -64.60
              Expenses:Financial Services        CHF 1.10
              Expenses:B                       CHF  63.50
        """)
        new = dedent("""\
            2021-04-27 * Coop
                Assets:Liquid:BCGE                 CHF -6.75
                Expenses:Gesundheit                   CHF 5.15
                Expenses:Groceries:C                  CHF 1.60

            2021/04/27 * Amazon -- Stuff
                Assets:Liquid:BCGE CC            CHF -64.60
                Expenses:Financial Services        CHF 1.10
                Expenses:Haushalt
        """)
        ed_diff = dedent("""\
            1c1,6
            < 2021-04-27 * AMZN Mktp DE, AMAZON.DE
            ---
            > 2021-04-27 * Coop
            >     Assets:Liquid:BCGE                 CHF -6.75
            >     Expenses:Gesundheit                   CHF 5.15
            >     Expenses:Groceries:C                  CHF 1.60
            > 
            > 2021/04/27 * Amazon -- Stuff
            4c9
            <   Expenses:B                       CHF  63.50
            ---
            >     Expenses:Haushalt
        """).strip()
        self.assertEqual(diff_ledger_text(original, new).strip(), ed_diff)


if __name__ == "__main__":
    unittest.main()
