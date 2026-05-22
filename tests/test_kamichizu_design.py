import unittest

from kamichizu import (
    Cell,
    FormatMap,
    SourceMap,
    SourceMeta,
    ViewMap,
    build_human_rows,
    build_semantic_rows,
    reconcile_sources,
)


def make_source(source_id, source_type, format_id, cells):
    return SourceMap(
        meta=SourceMeta(
            source_id=source_id,
            source_role="primary" if source_id.startswith("P") else "evidence",
            source_type=source_type,
            label=source_type,
            format_id=format_id,
        ),
        cells={cell_id: Cell(local_cell_id=cell_id, raw=str(value), value=value) for cell_id, value in cells.items()},
    )


class KamichizuDesignTest(unittest.TestCase):
    def test_physical_cell_id_rejects_semantic_names(self):
        with self.assertRaises(ValueError):
            Cell(local_cell_id="03_GEN")

        with self.assertRaises(ValueError):
            Cell(local_cell_id="03_MI")

    def test_format_map_assigns_meaning_to_physical_cells(self):
        paper = make_source("P01", "daily_report", "daily_a", {"03_AE": 1800, "03_AF": 2400})
        format_map = FormatMap(format_id="daily_a", columns={"AE": "gen", "AF": "mi"})

        rows = build_semantic_rows(paper, format_map)

        self.assertEqual(rows[0].value("gen"), 1800)
        self.assertEqual(rows[0].value("mi"), 2400)
        self.assertEqual(rows[0].fields["mi"].global_cell_id, "P01:03_AF")

    def test_semantic_rows_keep_blank_physical_addresses_for_observed_rows(self):
        paper = make_source("P01", "daily_report", "daily_a", {"03_AD": "10:44"})
        format_map = FormatMap(format_id="daily_a", columns={"AD": "time", "AE": "gen", "AF": "mi", "AG": "memo"})

        row = build_semantic_rows(paper, format_map)[0]

        self.assertEqual(row.value("time"), "10:44")
        self.assertIn("gen", row.fields)
        self.assertIn("mi", row.fields)
        self.assertIn("memo", row.fields)
        self.assertEqual(row.fields["gen"].local_cell_id, "03_AE")
        self.assertEqual(row.fields["mi"].global_cell_id, "P01:03_AF")
        self.assertEqual(row.fields["memo"].state, "blank")

    def test_same_physical_cell_changes_meaning_with_format_map(self):
        source = make_source("P01", "daily_report", "daily_a", {"03_AE": 1800})
        as_gen = FormatMap(format_id="daily_a", columns={"AE": "gen"})
        as_mi = FormatMap(format_id="daily_b", columns={"AE": "mi"})

        self.assertEqual(build_semantic_rows(source, as_gen)[0].value("gen"), 1800)
        self.assertEqual(build_semantic_rows(source, as_mi)[0].value("mi"), 1800)

    def test_layer2_uses_format_map_to_adopt_meter_amount_into_mi(self):
        paper = make_source(
            "P01",
            "daily_report",
            "daily_a",
            {
                "03_AB": 2,
                "03_AD": "10:44",
                "03_AF": 2400,
            },
        )
        paper_format = FormatMap(format_id="daily_a", columns={"AB": "passengers", "AD": "time", "AE": "gen", "AF": "mi"})
        meter = make_source("E01", "meter_receipt", "meter_a", {"05_AB": "10:44", "05_AC": 2430})
        meter_format = FormatMap(format_id="meter_a", columns={"AB": "time", "AC": "amount"})

        report = reconcile_sources(paper, paper_format, [(meter, meter_format)])

        row = report.rows[0]
        self.assertEqual(row.values["mi"], 2430)
        self.assertIsNone(row.values.get("gen"))
        self.assertEqual(row.evidence[0].paper_cell, "P01:03_AF")
        self.assertEqual(row.evidence[0].evidence_cell, "E01:05_AC")
        self.assertIn("paper amount 2400 adopted evidence amount 2430", report.diagnostics[0])

    def test_time_window_allows_nine_minutes_but_not_ten(self):
        paper = make_source("P01", "daily_report", "daily_a", {"03_AD": "10:44", "03_AE": 1000})
        paper_format = FormatMap(format_id="daily_a", columns={"AD": "time", "AE": "gen"})
        meter_ok = make_source("E01", "meter_receipt", "meter_a", {"05_AB": "10:53", "05_AC": 1000})
        meter_ng = make_source("E02", "meter_receipt", "meter_a", {"05_AB": "10:54", "05_AC": 1000})
        meter_format = FormatMap(format_id="meter_a", columns={"AB": "time", "AC": "amount"})

        ok_report = reconcile_sources(paper, paper_format, [(meter_ok, meter_format)])
        ng_report = reconcile_sources(paper, paper_format, [(meter_ng, meter_format)])

        self.assertEqual(ok_report.rows[0].values["gen"], 1000)
        self.assertFalse(ok_report.rows[0].alerts)
        self.assertEqual(ng_report.rows[0].alerts["gen"], "no_evidence_match")

    def test_layer2_adopts_meter_amount_when_paper_mi_amount_is_unreadable(self):
        paper = SourceMap(
            meta=SourceMeta(
                source_id="P01",
                source_role="primary",
                source_type="daily_report",
                label="daily_report",
                format_id="daily_a",
            ),
            cells={
                "03_AD": Cell(local_cell_id="03_AD", raw="10:44", value="10:44"),
                "03_AF": Cell(local_cell_id="03_AF", raw="?", value=None),
            },
        )
        paper_format = FormatMap(format_id="daily_a", columns={"AD": "time", "AE": "gen", "AF": "mi"})
        meter = make_source("E01", "meter_receipt", "meter_a", {"05_AB": "10:46", "05_AC": 2430})
        meter_format = FormatMap(format_id="meter_a", columns={"AB": "time", "AC": "amount"})

        report = reconcile_sources(paper, paper_format, [(meter, meter_format)])

        row = report.rows[0]
        self.assertEqual(row.values["mi"], 2430)
        self.assertEqual(row.evidence[0].paper_cell, "P01:03_AF")
        self.assertIn("paper amount unreadable adopted evidence amount 2430", report.diagnostics[0])

    def test_layer2_uses_payment_memo_as_mi_hint_when_amount_cell_is_not_read(self):
        paper = make_source(
            "P01",
            "daily_report",
            "daily_a",
            {
                "03_AD": "10:44",
                "03_AG": "Uber",
            },
        )
        paper_format = FormatMap(format_id="daily_a", columns={"AD": "time", "AF": "mi", "AG": "memo"})
        meter = make_source("E01", "meter_receipt", "meter_a", {"05_AB": "10:49", "05_AC": 2430})
        meter_format = FormatMap(format_id="meter_a", columns={"AB": "time", "AC": "amount"})

        report = reconcile_sources(paper, paper_format, [(meter, meter_format)])

        row = report.rows[0]
        self.assertEqual(row.values["mi"], 2430)
        self.assertEqual(row.values["memo"], "Uber")
        self.assertEqual(row.evidence[0].paper_cell, "P01:03_AG")

    def test_cash_memo_forces_cash_even_when_amount_was_observed_in_mi_column(self):
        paper = make_source(
            "P01",
            "daily_report",
            "daily_a",
            {
                "04_AD": "11:12",
                "04_AF": 1000,
                "04_AG": "現金",
            },
        )
        paper_format = FormatMap(format_id="daily_a", columns={"AD": "time", "AE": "gen", "AF": "mi", "AG": "memo"})
        meter = make_source("E01", "meter_receipt", "meter_a", {"04_AB": "11:12", "04_AC": 1000})
        meter_format = FormatMap(format_id="meter_a", columns={"AB": "time", "AC": "amount"})

        report = reconcile_sources(paper, paper_format, [(meter, meter_format)])

        row = report.rows[0]
        self.assertEqual(row.values["gen"], 1000)
        self.assertIsNone(row.values["mi"])
        self.assertEqual(row.values["memo"], "現金")
        self.assertEqual(row.evidence[0].paper_cell, "P01:04_AG")

    def test_cash_amount_without_mi_or_memo_adopts_as_cash(self):
        paper = make_source(
            "P01",
            "daily_report",
            "daily_a",
            {
                "03_AD": "10:44",
                "03_AE": 1800,
            },
        )
        paper_format = FormatMap(format_id="daily_a", columns={"AD": "time", "AE": "gen", "AF": "mi", "AG": "memo"})
        meter = make_source("E01", "meter_receipt", "meter_a", {"05_AB": "10:45", "05_AC": 1800})
        meter_format = FormatMap(format_id="meter_a", columns={"AB": "time", "AC": "amount"})

        report = reconcile_sources(paper, paper_format, [(meter, meter_format)])

        row = report.rows[0]
        self.assertEqual(row.values["gen"], 1800)
        self.assertIsNone(row.values.get("mi"))
        self.assertFalse(row.alerts)

    def test_dash_in_cash_column_does_not_force_cash_when_mi_has_amount(self):
        paper = SourceMap(
            meta=SourceMeta(
                source_id="P01",
                source_role="primary",
                source_type="daily_report",
                label="daily_report",
                format_id="daily_a",
            ),
            cells={
                "03_AD": Cell(local_cell_id="03_AD", raw="10:44", value="10:44"),
                "03_AE": Cell(local_cell_id="03_AE", raw="ー", value=None),
                "03_AF": Cell(local_cell_id="03_AF", raw="2400", value=2400),
            },
        )
        paper_format = FormatMap(format_id="daily_a", columns={"AD": "time", "AE": "gen", "AF": "mi"})
        meter = make_source("E01", "meter_receipt", "meter_a", {"05_AB": "10:46", "05_AC": 2430})
        meter_format = FormatMap(format_id="meter_a", columns={"AB": "time", "AC": "amount"})

        report = reconcile_sources(paper, paper_format, [(meter, meter_format)])

        row = report.rows[0]
        self.assertIsNone(row.values["gen"])
        self.assertEqual(row.values["mi"], 2430)
        self.assertEqual(row.evidence[0].paper_cell, "P01:03_AF")

    def test_voided_cash_cell_is_not_used_as_cash_value(self):
        paper = SourceMap(
            meta=SourceMeta(
                source_id="P01",
                source_role="primary",
                source_type="daily_report",
                label="daily_report",
                format_id="daily_a",
            ),
            cells={
                "03_AD": Cell(local_cell_id="03_AD", raw="10:44", value="10:44"),
                "03_AE": Cell(local_cell_id="03_AE", raw="2400", value=2400, marks=("strikethrough",)),
            },
        )
        paper_format = FormatMap(format_id="daily_a", columns={"AD": "time", "AE": "gen", "AF": "mi"})
        meter = make_source("E01", "meter_receipt", "meter_a", {"05_AB": "10:46", "05_AC": 2430})
        meter_format = FormatMap(format_id="meter_a", columns={"AB": "time", "AC": "amount"})

        report = reconcile_sources(paper, paper_format, [(meter, meter_format)])

        row = report.rows[0]
        self.assertIsNone(row.values["gen"])
        self.assertFalse(row.evidence)

    def test_voided_cash_cell_can_still_use_memo_as_mi_hint(self):
        paper = SourceMap(
            meta=SourceMeta(
                source_id="P01",
                source_role="primary",
                source_type="daily_report",
                label="daily_report",
                format_id="daily_a",
            ),
            cells={
                "03_AD": Cell(local_cell_id="03_AD", raw="10:44", value="10:44"),
                "03_AE": Cell(local_cell_id="03_AE", raw="2400", value=2400, state="voided"),
                "03_AG": Cell(local_cell_id="03_AG", raw="Uber", value="Uber"),
            },
        )
        paper_format = FormatMap(format_id="daily_a", columns={"AD": "time", "AE": "gen", "AF": "mi", "AG": "memo"})
        meter = make_source("E01", "meter_receipt", "meter_a", {"05_AB": "10:49", "05_AC": 2430})
        meter_format = FormatMap(format_id="meter_a", columns={"AB": "time", "AC": "amount"})

        report = reconcile_sources(paper, paper_format, [(meter, meter_format)])

        row = report.rows[0]
        self.assertIsNone(row.values["gen"])
        self.assertEqual(row.values["mi"], 2430)
        self.assertEqual(row.evidence[0].paper_cell, "P01:03_AG")

    def test_human_view_columns_are_view_map_not_engine_fixed(self):
        paper = make_source("P01", "daily_report", "daily_a", {"03_AD": "10:44", "03_AE": 1800})
        paper_format = FormatMap(format_id="daily_a", columns={"AD": "time", "AE": "gen"})
        meter = make_source("E01", "meter_receipt", "meter_a", {"05_AB": "10:44", "05_AC": 1800})
        meter_format = FormatMap(format_id="meter_a", columns={"AB": "time", "AC": "amount"})
        report = reconcile_sources(paper, paper_format, [(meter, meter_format)])

        view = ViewMap(view_id="taxi", columns=(("time", "時刻"), ("gen", "現収"), ("status", "状態")))

        self.assertEqual(build_human_rows(report, view), [{"時刻": "10:44", "現収": 1800, "状態": ""}])

    def test_unmatched_meter_evidence_reports_no_near_paper_row_reason(self):
        paper = make_source("P01", "daily_report", "daily_a", {"03_AD": "10:44", "03_AE": 1800})
        paper_format = FormatMap(format_id="daily_a", columns={"AD": "time", "AE": "gen"})
        meter = make_source(
            "E01",
            "meter_receipt",
            "meter_a",
            {"08_AB": "17:08", "08_AC": 1200},
        )
        meter_format = FormatMap(format_id="meter_a", columns={"AB": "time", "AC": "amount"})

        report = reconcile_sources(paper, paper_format, [(meter, meter_format)])

        self.assertIn("unmatched evidence E01:08", report.diagnostics[0])
        self.assertIn("reason=no_paper_time_within_9_minutes", report.diagnostics[0])
        self.assertIn("time=17:08", report.diagnostics[0])
        self.assertIn("amount=1200", report.diagnostics[0])

    def test_blank_payment_cells_default_to_cash_when_unique_meter_time_matches(self):
        paper = make_source("P01", "daily_report", "daily_a", {"03_AD": "10:44", "03_AB": 2})
        paper_format = FormatMap(format_id="daily_a", columns={"AB": "passengers", "AD": "time", "AE": "gen", "AF": "mi", "AG": "memo"})
        meter = make_source("E01", "meter_receipt", "meter_a", {"05_AB": "10:46", "05_AC": 2430})
        meter_format = FormatMap(format_id="meter_a", columns={"AB": "time", "AC": "amount"})

        report = reconcile_sources(paper, paper_format, [(meter, meter_format)])

        row = report.rows[0]
        self.assertEqual(row.values["gen"], 2430)
        self.assertIsNone(row.values["mi"])
        self.assertEqual(row.evidence[0].paper_cell, "P01:03_AE")
        self.assertFalse(row.alerts)
        self.assertEqual(report.diagnostics, ())

    def test_unreadable_payment_memo_does_not_default_to_cash(self):
        paper = make_source("P01", "daily_report", "daily_a", {"03_AD": "10:44", "03_AB": 2, "03_AG": "?"})
        paper_format = FormatMap(format_id="daily_a", columns={"AB": "passengers", "AD": "time", "AE": "gen", "AF": "mi", "AG": "memo"})
        meter = make_source("E01", "meter_receipt", "meter_a", {"05_AB": "10:46", "05_AC": 2430})
        meter_format = FormatMap(format_id="meter_a", columns={"AB": "time", "AC": "amount"})

        report = reconcile_sources(paper, paper_format, [(meter, meter_format)])

        self.assertIn("unmatched evidence E01:05", report.diagnostics[0])
        self.assertIn("reason=paper_time_match_without_payment_destination", report.diagnostics[0])
        self.assertIn("near_paper=03@2m", report.diagnostics[0])


if __name__ == "__main__":
    unittest.main()
