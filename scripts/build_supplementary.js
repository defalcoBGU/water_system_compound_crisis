// Build multicrisis_supplementary_FINAL.docx with docx-js.
// All numeric cells come from results/earth_future_revision/task{0..6}/ outputs.
// No values are estimated. Tables S1, S2, Text S1-S3 preserved from the
// user's original supplementary_materials-2-2.docx where their content is
// still correct under the revision. Tables S3-S8 and Figures S1/S2/S6/S7
// reflect new runs documented in MANUSCRIPT_CORRECTIONS.md entries C1-C13.

const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, LevelFormat, PageBreak, PageOrientation
} = require('docx');

const REPO = '/Users/karolbot/projects/outdated_projects/finaldt_v4';
const OUT_DIR = path.join(REPO, 'results', 'earth_future_revision');

// ----- style primitives -----
const border = { style: BorderStyle.SINGLE, size: 4, color: '999999' };
const cellBorders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };
const headerShade = { fill: 'D9E2F3', type: ShadingType.CLEAR, color: 'auto' };

function para(text, opts = {}) {
  const runs = Array.isArray(text) ? text : [new TextRun({ text, ...opts })];
  return new Paragraph({ children: runs, spacing: { after: 120 }, ...opts.paragraphProps });
}
function bold(text) { return new TextRun({ text, bold: true }); }
function italic(text) { return new TextRun({ text, italics: true }); }
function plain(text) { return new TextRun({ text }); }
function h1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text, bold: true, size: 28 })],
    spacing: { before: 280, after: 160 } });
}
function h2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text, bold: true, size: 24 })],
    spacing: { before: 200, after: 120 } });
}
function caption(text) {
  return new Paragraph({
    children: [new TextRun({ text, italics: true, size: 20 })],
    spacing: { after: 200 } });
}

function cell(content, opts = {}) {
  const { width, header = false, colSpan } = opts;
  const children = Array.isArray(content)
    ? content.map(c => typeof c === 'string' ? para(c) : c)
    : [typeof content === 'string' ? para(content) : content];
  const cellOpts = {
    borders: cellBorders,
    margins: cellMargins,
    children,
  };
  if (width) cellOpts.width = { size: width, type: WidthType.DXA };
  if (header) cellOpts.shading = headerShade;
  if (colSpan) cellOpts.columnSpan = colSpan;
  return new TableCell(cellOpts);
}

function headerCell(text, width) {
  return cell([new Paragraph({
    children: [new TextRun({ text, bold: true })],
  })], { width, header: true });
}

// Full-width table: 9360 DXA for US Letter with 1" margins
const TABLE_WIDTH = 9360;
function table(columnWidths, rows) {
  return new Table({
    width: { size: TABLE_WIDTH, type: WidthType.DXA },
    columnWidths,
    rows: rows.map(r => new TableRow({ children: r, cantSplit: false })),
  });
}

function imgFromPath(filePath, widthInches, heightInches) {
  if (!fs.existsSync(filePath)) {
    return para(`[FIGURE FILE MISSING: ${filePath}]`);
  }
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new ImageRun({
      type: 'png',
      data: fs.readFileSync(filePath),
      transformation: { width: widthInches * 72, height: heightInches * 72 },
      altText: { title: path.basename(filePath), description: path.basename(filePath), name: path.basename(filePath) },
    })],
  });
}

// ----- content builders -----

function titleBlock() {
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: 'Supplementary Materials', bold: true, size: 36 })],
      spacing: { after: 160 }
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({
        text: 'Compound Security–Climate Vulnerability of a Desalination-Dependent Water System: Scenario Analysis for Israel',
        italics: true, size: 26
      })],
      spacing: { after: 280 }
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({
        text: 'Karol Bot, Natalie De Falco, Jürgen Renn, Noam Weisbrod',
        size: 22
      })],
      spacing: { after: 400 }
    }),
  ];
}

function contentsBlock() {
  const items = [
    'Table S1. Crisis typology justification and impact mechanisms',
    'Table S2. Severity parameterization for crisis types',
    'Table S3. Crisis parameter values and sources',
    'Table S4. Top 15 most severe compound scenarios (Tier 3 Monte Carlo)',
    'Table S5. Literature benchmark of single-crisis impacts against published figures — TEMPLATE',
    'Table S6. Demand elasticity ±50 % sensitivity on the four-pessimistic worst case',
    'Table S7. Response-category triggering by impact cluster (Tier 3)',
    'Table S8. Retrospective grounding year-by-year data (2010–2018)',
    'Figure S1. Top 15 most severe compound scenarios (Tier 3, n=500 MC draws)',
    'Figure S2. Monte Carlo distribution of worst-case supply reduction at each γ tier',
    'Figure S6. Alternative WSI-convention robustness scatter',
    'Figure S7. Response-threshold ±20 % sensitivity across 243 scenarios',
    'Text S1. Extended hydrological foundations',
    'Text S2. Framework transferability considerations',
    'Text S3. Complete reference list',
  ];
  return [
    h1('Contents'),
    ...items.map(s => new Paragraph({
      children: [new TextRun({ text: s, size: 22 })],
      spacing: { after: 60 }
    })),
    new Paragraph({ children: [new PageBreak()] }),
  ];
}

// Table S1 — crisis typology (from original supp, preserved)
function tableS1() {
  const rows = [
    [headerCell('Crisis Type', 1500), headerCell('Primary Mechanism', 2800),
     headerCell('Affected Components', 3060), headerCell('Duration Profile', 2000)],
    [cell('Hydrological Drought', { width: 1500 }),
     cell('Precipitation deficit reduces recharge and surface flows', { width: 2800 }),
     cell('Surface water, groundwater, reservoir storage', { width: 3060 }),
     cell('Multi-year (sustained)', { width: 2000 })],
    [cell('Energy Disruption', { width: 1500 }),
     cell('Supply shortage constrains energy-intensive operations', { width: 2800 }),
     cell('Desalination, pumping, treatment', { width: 3060 }),
     cell('Months to years (episodic)', { width: 2000 })],
    [cell('Armed Conflict', { width: 1500 }),
     cell('Physical damage to infrastructure; demand disruption', { width: 2800 }),
     cell('All physical infrastructure; cross-border resources', { width: 3060 }),
     cell('Variable (event-dependent)', { width: 2000 })],
    [cell('Cyber Attack', { width: 1500 }),
     cell('Compromise of control systems; operational disruption', { width: 2800 }),
     cell('SCADA systems; desalination control; distribution', { width: 3060 }),
     cell('Days to months (acute)', { width: 2000 })],
  ];
  return [
    h2('Table S1. Crisis Typology Justification'),
    para('The selection of four crisis types reflects three considerations: coverage of system dependencies, alignment with contemporary threat assessment, and demonstrated occurrence.'),
    table([1500, 2800, 3060, 2000], rows),
    para([plain('Coverage of system dependencies: '), plain('Modern integrated water systems depend on natural water availability, energy supply, physical infrastructure integrity, and digital control systems. Each dependency constitutes a potential failure pathway. The four-type scheme provides minimal coverage while maintaining analytical tractability.')]),
    para([plain('Alignment with threat assessment: '), plain('The selected crisis types align with those emphasized in the IPCC Sixth Assessment Report (Caretta et al., 2022), energy-water nexus literature (Bazilian et al., 2011), conflict documentation (Gleick, 2014; 2019), and national security frameworks (CISA, 2024).')]),
    para([plain('Demonstrated occurrence: '), plain('Each crisis type has documented precedent: multi-year droughts across the Mediterranean, Australia, California (Spinoni et al., 2018); energy cascades during Texas 2021 (Busby et al., 2021); infrastructure damage in Syria, Yemen, Ukraine (Gleick, 2019); cyber intrusions targeting water sector in the US and Israel (Hassanzadeh et al., 2020).')]),
  ];
}

// Table S2 — severity parameterization (preserved)
function tableS2() {
  const rows = [
    [headerCell('Severity Level', 1800), headerCell('Description', 7560)],
    [cell('Optimistic', { width: 1800 }),
     cell('Crisis occurs with limited intensity or effective mitigation. System impacts noticeable but manageable within normal operational flexibility. Represents lower bound on impact given crisis occurrence.', { width: 7560 })],
    [cell('Moderate', { width: 1800 }),
     cell('Crisis occurs with substantial intensity, straining system capacity but not overwhelming it. Operational adjustments and contingency measures required; some service degradation may occur. Represents central tendency among plausible manifestations.', { width: 7560 })],
    [cell('Pessimistic', { width: 1800 }),
     cell('Crisis occurs with severe intensity or poor mitigation. System capacity exceeded in some respects; emergency measures required; significant service impacts result. Represents upper bound on plausible impact short of complete system failure.', { width: 7560 })],
  ];
  return [
    h2('Table S2. Severity Parameterization'),
    para('Each crisis type manifests across a spectrum of intensity. The three-level severity scheme spans the plausible range based on historical precedent.'),
    table([1800, 7560], rows),
  ];
}

// Table S3 — crisis parameter values (UPDATED per C10)
function tableS3() {
  const rows = [
    [headerCell('Crisis Type', 1700), headerCell('Optimistic', 2553),
     headerCell('Moderate', 2553), headerCell('Pessimistic', 2554)],
    [cell('Drought', { width: 1700 }),
     cell('20 % reduction in surface water and groundwater availability', { width: 2553 }),
     cell('40 % reduction in surface water and groundwater availability', { width: 2553 }),
     cell('60 % reduction in surface water and groundwater availability', { width: 2554 })],
    [cell('Energy disruption', { width: 1700 }),
     cell('5 % reduction in desalination capacity (factor 0.95)', { width: 2553 }),
     cell('15 % reduction in desalination capacity (factor 0.85)', { width: 2553 }),
     cell('30 % reduction in desalination capacity (factor 0.70)', { width: 2554 })],
    [cell('Armed conflict', { width: 1700 }),
     cell('15 % reduction to all supply sources; demand changes: agricultural −5 %, domestic 0 %, industrial −2 %', { width: 2553 }),
     cell('30 % reduction to all supply sources; demand changes: agricultural −15 %, domestic −3 %, industrial −5 %', { width: 2553 }),
     cell('60 % reduction to all supply sources; demand changes: agricultural −30 %, domestic −10 %, industrial −20 %', { width: 2554 })],
    [cell('Cyber-attack', { width: 1700 }),
     cell('1 % desalination downtime; 10 % affected-supply proportion (infrastructure fully affected, natural sources at half the fraction)', { width: 2553 }),
     cell('5 % desalination downtime; 20 % affected-supply proportion', { width: 2553 }),
     cell('10 % desalination downtime; 50 % affected-supply proportion', { width: 2554 })],
  ];
  return [
    h2('Table S3. Crisis Parameter Values'),
    para('Parameter values operationalise severity levels as modification factors applied to supply or demand components. All values are from the repository CSV files drought_params.csv, energy_params.csv, conflict_params.csv, cyber_params.csv; the table below reports the derived percentage reductions for readability.'),
    table([1700, 2553, 2553, 2554], rows),
    para([bold('Important interpretive note on drought parameters (updated for this revision).'),
          plain(' The drought reduction percentages represent unmitigated natural-source availability shocks, not observed extraction under operational management. The retrospective grounding against the 2013–2016 Levant drought (Results §3.2 and Table S8) shows observed natural-source extraction declined only 10.8 % over that window, even though the drought met the definitional criteria of a multi-year hydrological event, because Israel Water Authority operational practice (groundwater preservation, desalination substitution, including Sorek 2013 and Ashdod 2015 commissioning) buffered the extraction shortfall. Users applying the framework to other water systems should either document this availability-versus-extraction distinction explicitly or re-anchor Moderate and Pessimistic drought parameters to events whose observed natural-source declines match the modelled 40 % and 60 % reductions.')]),
    para([bold('Sources. '),
          plain('Drought parameters reflect Mediterranean drought severity ranges (Spinoni et al., 2018; Cook et al., 2018). Energy parameters reflect operational constraints observed during shortage events (Busby et al., 2021). Conflict parameters reflect documented infrastructure damage in regional conflicts (Gleick, 2014; 2019). Cyber parameters reflect assessed vulnerability ranges (Hassanzadeh et al., 2020; Shapira et al., 2021).')]),
  ];
}

// Table S4 — Top 15 Tier 3 scenarios (NEW data)
function tableS4() {
  // Values from results/earth_future_revision/supp_figures/table_s4_top15_tier3.csv
  const data = [
    ['1', 'DP+EP+CP+YP', '88.62', '84.70–92.04', '9.92', '−1755', '4', '1.53'],
    ['2', 'DP+EM+CP+YP', '87.73', '83.37–91.21', '9.92', '−1731', '3', '1.53'],
    ['3', 'DP+EO+CP+YP', '87.08', '82.72–90.69', '9.92', '−1713', '3', '1.53'],
    ['4', 'DM+EP+CP+YP', '86.61', '82.01–90.46', '7.48', '−1701', '3', '1.53'],
    ['5', 'DP+EP+CP+YM', '85.73', '81.56–89.69', '6.78', '−1677', '3', '1.53'],
    ['6', 'DM+EM+CP+YP', '85.72', '80.76–89.86', '7.48', '−1677', '2', '1.53'],
    ['7', 'DM+EO+CP+YP', '85.07', '79.97–89.46', '7.48', '−1659', '2', '1.53'],
    ['8', 'DP+EM+CP+YM', '84.79', '80.21–88.94', '6.78', '−1651', '2', '1.53'],
    ['9', 'DP+EP+CP+YO', '84.63', '80.11–88.87', '6.09', '−1647', '3', '1.53'],
    ['10', 'DO+EP+CP+YP', '84.58', '78.94–89.26', '5.87', '−1646', '3', '1.53'],
    ['11', 'DP+EO+CP+YM', '84.09', '79.31–88.39', '6.78', '−1632', '2', '1.53'],
    ['12', 'DP+CP+YP',    '84.06', '79.24–88.45', '7.96', '−1631', '3', '1.265'],
    ['13', 'DO+EM+CP+YP', '83.70', '77.71–88.54', '5.87', '−1622', '2', '1.53'],
    ['14', 'DP+EM+CP+YO', '83.65', '78.91–87.91', '6.09', '−1620', '2', '1.53'],
    ['15', 'DM+EP+CP+YM', '83.32', '78.11–87.80', '5.21', '−1611', '2', '1.53'],
  ];
  const rows = [
    [headerCell('Rank', 700),
     headerCell('Scenario', 1600),
     headerCell('Supply reduction (%)', 1600),
     headerCell('95 % CI (%)', 1600),
     headerCell('ΔWSI', 800),
     headerCell('ΔGap (MCM)', 1200),
     headerCell('Pes count', 860),
     headerCell('γ product', 1000)],
    ...data.map(r => r.map((v, i) => cell(v, { width: [700, 1600, 1600, 1600, 800, 1200, 860, 1000][i] }))),
  ];
  return [
    h2('Table S4. Top 15 Most Severe Compound Scenarios (Tier 3 Monte Carlo, n = 500 draws per scenario)'),
    para('Scenarios ranked by mean supply reduction at Tier 3 γ values (central estimates from Table 1 of the main text). 95 % confidence intervals are percentile-based on the Monte Carlo sample (±25 % uniform on severity parameters, seed 20260423). γ product is the product of documented γ values for the active interaction pairs in each scenario composition.'),
    table([700, 1600, 1600, 1600, 800, 1200, 860, 1000], rows),
    para([italic('Scenario codes: D = Drought, E = Energy, C = Conflict, Y = Cyber; O = Optimistic, M = Moderate, P = Pessimistic. Every top-15 scenario contains Pessimistic conflict (CP); 9 of 15 contain Pessimistic cyber (YP); γ product reaches its maximum 1.53 when all four documented interaction pairs are active (four-crisis compositions). Source: results/earth_future_revision/task2/tier3_scenario_results.csv.')]),
  ];
}

// Table S5 — Literature benchmark of single-crisis impacts against published figures
// Published figures extracted from primary sources during the 2026-04-24 research pass.
// The Gleick 2014 figures are commonly cited and consistent across secondary summaries
// but were not directly verified against the paper PDF in that session — flagged accordingly.
function tableS5() {
  const rows = [
    [headerCell('Event', 2200),
     headerCell('Primary source', 1800),
     headerCell('Published impact (verbatim, units)', 2600),
     headerCell('Modelled severity at closest comparator', 1560),
     headerCell('Match category', 1200)],
    [cell('2021 Texas winter storm (Uri) — energy–water cascade', { width: 2200 }),
     cell('Busby et al. 2021 (Introduction; Ref 6); PLOS Water Patel et al. 2024 secondary', { width: 1800 }),
     cell('"Boil-water notices for more than 14 million people" (Busby et al. 2021); 2,038 public water systems issued advisories, mean duration 7.96 days (SD 3.57); >17 million people affected (Patel et al. 2024). Upstream driver: >30 GW of generating capacity unavailable versus 14 GW extreme-winter planning scenario.', { width: 2600 }),
     cell('Energy Pessimistic: 30 % desalination capacity loss', { width: 1560 }),
     cell('Outside meaningful comparison — published metric is "boil-water notice exposure", not % supply reduction; no direct quantitative translation without a system-specific assumption.', { width: 1200 })],
    [cell('2018 Cape Town "Day Zero" drought', { width: 2200 }),
     cell('Pascale et al. 2020 (Ref 9); Booysen et al. 2019 (Ref 10) secondary', { width: 1800 }),
     cell('Reservoir storage dropped to ~20 % of capacity in May 2018 (i.e. ~80 % storage deficit); Day-Zero shutoff threshold set at 13.5 % capacity; rainfall anomaly −11.5 mm/month averaged across three observational datasets for 2015–2017; three consecutive dry winters (Pascale et al. 2020). Household water use fell from 540 to 280 L/household/day over Jan 2015–Jan 2018 (~48 % demand reduction; Booysen et al. 2019).', { width: 2600 }),
     cell('Drought Pessimistic: 60 % natural-source availability reduction', { width: 1560 }),
     cell('Model under-predicts observed storage deficit by roughly 20 percentage points (60 % modelled vs ~80 % observed); this direction of bias is opposite to the Levant retrospective (Section 3.2), consistent with the Pessimistic severity being anchored to mid-range rather than to the most severe documented reservoir collapse. Household demand response (−48 %) exceeds the modelled conflict-linked agricultural demand elasticity (−30 % Pessimistic); different crisis type — direct comparison not applicable.', { width: 1200 })],
    [cell('2021 Oldsmar, Florida water-treatment cyber attack', { width: 2200 }),
     cell('CISA Advisory AA21-042A (2021-02-11); Pinellas County Sheriff public statements. Hassanzadeh et al. 2020 (Ref 7) cited for framework, not for Oldsmar-specific figures.', { width: 1800 }),
     cell('Sodium-hydroxide setpoint changed from 100 ppm to 11,100 ppm (111-fold increase; "more than 100 times normal levels"); intrusion duration ~5 minutes; operator reversed change in real time; estimated chemical propagation time to consumers 24–36 hours; zero documented consumer exposure (CISA AA21-042A).', { width: 2600 }),
     cell('Cyber Pessimistic: 10 % desalination downtime + 50 % affected-supply proportion on infrastructure sources', { width: 1560 }),
     cell('Outside meaningful comparison — near-miss with zero delivered supply impact; published metric is magnitude of setpoint manipulation (111×), not supply reduction. The modelled Cyber Pessimistic parameters represent a counterfactual where operator intervention fails, which is not what happened at Oldsmar.', { width: 1200 })],
    [cell('Syrian pre-conflict water stress (2006–2011)', { width: 2200 }),
     cell('Gleick 2014 (Ref 4); Van Loon et al. 2016 (Ref 11) secondary', { width: 1800 }),
     cell('"Easily the driest [winter] in the observed records" (2007/2008 winter; Gleick 2014); reported yield declines of ~47 % (wheat) and ~67 % (barley) during 2006–2009; ~1.3 million people in eastern Syria affected; ~800,000 lost livelihoods/food supports; internal displacement up to ~1.5 million; near-total herd loss for small and medium herders (Gleick 2014 secondary summaries — primary PDF unverified in the research pass; figures consistent across secondary literature but should be cross-checked against DOI 10.1175/WCAS-D-13-00059.1 pp. 334–336 before publication).', { width: 2600 }),
     cell('Drought Pessimistic: 60 % natural-source availability reduction; Conflict Pessimistic: 60 % supply-capacity loss + sector demand changes', { width: 1560 }),
     cell('Outside meaningful comparison — published metrics are agricultural-output and humanitarian-displacement outcomes, not % water-supply reduction at the utility/balance level. A direct comparison would require an intermediate crop-water or food-system translation that is outside the scope of the water-balance framework. The framework\'s relevance is upstream (supply shock under drought) — the Syrian case illustrates the cascade pathway without providing a comparable supply-reduction datum.', { width: 1200 })],
  ];
  return [
    h2('Table S5. Literature Benchmark of Single-Crisis Impacts against Published Figures'),
    para([plain('Documented impact figures from the four events already cited in the main-text reference list, compared with the closest single-crisis modelled severity. Published figures are quoted verbatim (with units) from the primary source where feasible. Three of four events produce metrics that are not directly comparable to the % supply-reduction output of the model (boil-water exposure counts, chemical setpoint manipulation, downstream agricultural outcomes) — a common situation when matching idealised water-balance models against heterogeneous documented impacts. The Cape Town case is the most directly comparable and indicates that the Pessimistic drought severity parameterisation is modest relative to the most severe documented reservoir collapse; combined with the Levant retrospective grounding (Section 3.2), this brackets the Pessimistic level between observed operational outcomes (Levant, 10.8 % decline) and observed storage collapse (Cape Town, ~80 % reservoir deficit) as an intermediate unmitigated-availability stress anchor.')]),
    table([2200, 1800, 2600, 1560, 1200], rows),
    para([italic('Match-category definitions. "Within range": published value falls within the modelled CI for the matching severity. "Model over- / under-predicts by X %": quantitative disagreement in the same metric. "Outside meaningful comparison": the published impact is measured in units or at a causal stage that cannot be mapped onto the model\'s % supply-reduction without an external translation assumption.')]),
    para([bold('Sources used beyond the main-text reference list: '),
          plain('CISA Advisory AA21-042A (U.S. Department of Homeland Security, 2021-02-11); Pinellas County Sheriff public statements (2021-02-08); Patel et al. 2024 "Disparities in drinking water disruptions during Winter Storm Uri", PLOS Water; PNAS Open Access PMC7703628 for Pascale et al. 2020; PubMed 30472543 for Booysen et al. 2019. The Syrian-drought figures are consistent across secondary summaries of Gleick 2014 but the primary PDF (DOI 10.1175/WCAS-D-13-00059.1) could not be fetched in the research pass; co-authors should verify the 47 % / 67 % / 1.5 million figures against the original before submission.')]),
  ];
}

// Table S6 — demand elasticity ±50 % (NEW from task4)
function tableS6() {
  // Pre-computed from task4/table_s6_demand_elasticity.csv
  // Supply reduction is invariant; only WSI and gap_change respond.
  const rows = [
    [headerCell('Parameter (Pessimistic severity)', 2200),
     headerCell('Base', 900),
     headerCell('×0.5', 900),
     headerCell('×1.0', 900),
     headerCell('×1.5', 900),
     headerCell('Range', 900),
     headerCell('Metric', 2660)],
    [cell('AgriculturalDemandChange', { width: 2200 }), cell('−0.30', { width: 900 }),
     cell('88.74', { width: 900 }), cell('88.74', { width: 900 }), cell('88.74', { width: 900 }),
     cell('0.00', { width: 900 }),
     cell('Supply reduction (%) — invariant', { width: 2660 })],
    [cell('DomesticDemandChange', { width: 2200 }), cell('−0.10', { width: 900 }),
     cell('88.74', { width: 900 }), cell('88.74', { width: 900 }), cell('88.74', { width: 900 }),
     cell('0.00', { width: 900 }),
     cell('Supply reduction (%) — invariant', { width: 2660 })],
    [cell('IndustrialDemandChange', { width: 2200 }), cell('−0.20', { width: 900 }),
     cell('88.74', { width: 900 }), cell('88.74', { width: 900 }), cell('88.74', { width: 900 }),
     cell('0.00', { width: 900 }),
     cell('Supply reduction (%) — invariant', { width: 2660 })],

    [cell('AgriculturalDemandChange', { width: 2200 }), cell('−0.30', { width: 900 }),
     cell('10.94', { width: 900 }), cell('9.64', { width: 900 }), cell('8.35', { width: 900 }),
     cell('2.59', { width: 900 }),
     cell('ΔWSI (absolute)', { width: 2660 })],
    [cell('DomesticDemandChange', { width: 2200 }), cell('−0.10', { width: 900 }),
     cell('9.82', { width: 900 }), cell('9.64', { width: 900 }), cell('9.46', { width: 900 }),
     cell('0.36', { width: 900 }),
     cell('ΔWSI (absolute)', { width: 2660 })],
    [cell('IndustrialDemandChange', { width: 2200 }), cell('−0.20', { width: 900 }),
     cell('9.86', { width: 900 }), cell('9.64', { width: 900 }), cell('9.43', { width: 900 }),
     cell('0.43', { width: 900 }),
     cell('ΔWSI (absolute)', { width: 2660 })],

    [cell('AgriculturalDemandChange', { width: 2200 }), cell('−0.30', { width: 900 }),
     cell('−2008', { width: 900 }), cell('−1758', { width: 900 }), cell('−1508', { width: 900 }),
     cell('500', { width: 900 }),
     cell('ΔGap (MCM/yr)', { width: 2660 })],
    [cell('DomesticDemandChange', { width: 2200 }), cell('−0.10', { width: 900 }),
     cell('−1793', { width: 900 }), cell('−1758', { width: 900 }), cell('−1724', { width: 900 }),
     cell('69', { width: 900 }),
     cell('ΔGap (MCM/yr)', { width: 2660 })],
    [cell('IndustrialDemandChange', { width: 2200 }), cell('−0.20', { width: 900 }),
     cell('−1800', { width: 900 }), cell('−1758', { width: 900 }), cell('−1717', { width: 900 }),
     cell('83', { width: 900 }),
     cell('ΔGap (MCM/yr)', { width: 2660 })],
  ];
  return [
    h2('Table S6. Demand Elasticity ±50 % Sensitivity (Four-Pessimistic Worst Case, Tier 3)'),
    para([plain('Each row reports the four-pessimistic scenario (all crisis types at Pessimistic severity, Tier 3 γ values) under a single parameter perturbation. '),
          bold('Supply reduction is invariant to demand-change parameters by construction'),
          plain(' (demand changes modify demand, not supply); the informative responses are ΔWSI and ΔGap. Source: results/earth_future_revision/task4/table_s6_demand_elasticity.csv.')]),
    table([2200, 900, 900, 900, 900, 900, 2660], rows),
    para([italic('Agricultural demand-change dominates both WSI (2.59-unit range across ±50 %) and gap (500 MCM/yr range), consistent with its large negative base value (−30 %) and agriculture\'s share of total demand. Domestic and industrial elasticities produce sub-10 % of that sensitivity in ΔGap.')]),
  ];
}

// Table S7 — response category triggering by impact cluster (Tier 3)
function tableS7() {
  // Computed: Low (n=61) / Medium (n=121) / High (n=61) from task2/tier3_scenario_results.csv
  const rows = [
    [headerCell('Response category', 2500),
     headerCell('Low (n=61)', 1715),
     headerCell('Medium (n=121)', 1715),
     headerCell('High (n=61)', 1715),
     headerCell('Overall (n=243)', 1715)],
    [cell('Supply Expansion (>40 % supply reduction)', { width: 2500 }),
     cell('31.1 %', { width: 1715 }), cell('100.0 %', { width: 1715 }),
     cell('100.0 %', { width: 1715 }), cell('82.7 %', { width: 1715 })],
    [cell('Sustainability Measures (ΔWSI > 0.5)', { width: 2500 }),
     cell('72.1 %', { width: 1715 }), cell('100.0 %', { width: 1715 }),
     cell('100.0 %', { width: 1715 }), cell('93.0 %', { width: 1715 })],
    [cell('Emergency Measures (gap below ensemble median)', { width: 2500 }),
     cell('0.0 %', { width: 1715 }), cell('55.4 %', { width: 1715 }),
     cell('88.5 %', { width: 1715 }), cell('49.8 %', { width: 1715 })],
    [cell('Resilience Hardening (conflict or cyber at Moderate+)', { width: 2500 }),
     cell('41.0 %', { width: 1715 }), cell('84.3 %', { width: 1715 }),
     cell('100.0 %', { width: 1715 }), cell('77.4 %', { width: 1715 })],
    [cell('Mean responses per scenario', { width: 2500 }),
     cell('1.4', { width: 1715 }), cell('3.4', { width: 1715 }),
     cell('3.9', { width: 1715 }), cell('3.0', { width: 1715 })],
  ];
  return [
    h2('Table S7. Response-Category Triggering by Impact Cluster (Tier 3)'),
    para([plain('Impact clusters are defined by quartiles of the Tier 3 mean supply reduction: Low ≤ 46.5 %, Medium 46.5–73.0 %, High ≥ 73.0 %. Supply Expansion and Sustainability Measures trigger in every Medium- and High-impact scenario; Emergency Measures is concentrated in the tail; Resilience Hardening is triggered whenever security crises appear at Moderate or Pessimistic severity, hence rises steeply with impact-cluster severity. Source: results/earth_future_revision/task2/tier3_scenario_results.csv (re-aggregation by quartile; code in the main manuscript update trail).')]),
    table([2500, 1715, 1715, 1715, 1715], rows),
  ];
}

// Table S8 — retrospective year-by-year
function tableS8() {
  // From results/earth_future_revision/task1/table_s8_retrospective_data.csv
  const data = [
    ['2010','1003','2020','1003','796','1955','597','1756','398','1557','100.8','98.2'],
    ['2011','934','1957','934','796','1955','597','1756','398','1557','93.9','95.1'],
    ['2012','995','2057','995','796','1955','597','1756','398','1557','100.0','100.0'],
    ['2013','890','2106','398','398','1557','398','1557','398','1557','89.4','102.4'],
    ['2014','926','2085','398','398','1557','398','1557','398','1557','93.1','101.4'],
    ['2015','842','2152','398','398','1557','398','1557','398','1557','84.6','104.6'],
    ['2016','892','2253','398','398','1557','398','1557','398','1557','89.7','109.5'],
    ['2017','896','2307','896','796','1955','597','1756','398','1557','90.0','112.1'],
    ['2018','787','2271','787','796','1955','597','1756','398','1557','79.1','110.4'],
  ];
  const rows = [
    [headerCell('Year', 700),
     headerCell('Obs natural (MCM)', 1200),
     headerCell('Obs total (MCM)', 1100),
     headerCell('Mod Opt natural', 900),
     headerCell('Mod Mod natural', 900),
     headerCell('Mod Pes natural', 900),
     headerCell('Mod Opt total', 900),
     headerCell('Mod Mod total', 900),
     headerCell('% of 2012 natural (obs)', 900),
     headerCell('% of 2012 total (obs)', 960)],
    ...data.map(r => {
      const picked = [r[0], r[1], r[2], r[3], r[5], r[7], r[4], r[6], r[10], r[11]];
      return picked.map((v, i) => cell(v, { width: [700, 1200, 1100, 900, 900, 900, 900, 900, 900, 960][i] }));
    }),
  ];
  return [
    h2('Table S8. Retrospective Grounding — Year-by-Year Data (2010–2018)'),
    para('Year-by-year natural-source and total-supply values for the retrospective-grounding window. "Obs" columns are the Israel Water Authority annual balance data; "Mod Opt/Mod/Pes" columns are the modelled trajectories at the three severity levels with the crisis window shifted from 2030–2032 to 2013–2016. Baseline year 2012; percent-of-2012 columns normalise each series to the pre-drought baseline. Source: results/earth_future_revision/task1/table_s8_retrospective_data.csv.'),
    table([700, 1200, 1100, 900, 900, 900, 900, 900, 900, 960], rows),
    para([italic('Note: Observed total supply rose over the crisis window (104–110 % of 2012 baseline) because Sorek desalination (2013) and Ashdod desalination (2015) came online during the drought, compensating for the natural-source decline. The modelled total-supply columns (Mod Opt total / Mod Mod total / Mod Pes total — last three columns truncated from this view; see CSV for full precision) show the counterfactual trajectory had those expansions not occurred.')]),
  ];
}

// Figures - each with caption only; images embedded inline
function figureS1() {
  const imgPath = path.join(REPO, 'results', 'earth_future_revision', 'supp_figures', 'figure_s1_top15_scenarios.png');
  return [
    h2('Figure S1. Top 15 Most Severe Compound Scenarios (Tier 3, n=500 MC draws)'),
    imgFromPath(imgPath, 6.0, 5.0),
    caption('Figure S1. Top 15 most severe compound scenarios ranked by Tier 3 mean supply reduction with 95 % confidence intervals (±25 % uniform MC on severity parameters, seed 20260423). Bar colour encodes the number of Pessimistic crises in the composition. Every top-15 scenario contains Pessimistic conflict (CP); 9 of 15 also contain Pessimistic cyber (YP). Scenario codes: D=Drought, E=Energy, C=Conflict, Y=Cyber; O=Optimistic, M=Moderate, P=Pessimistic. Source files: results/earth_future_revision/supp_figures/figure_s1_top15_scenarios.{pdf,png,svg}.'),
  ];
}

function figureS2() {
  const imgPath = path.join(REPO, 'results', 'earth_future_revision', 'task2', 'figure_s2_tiered_mc.png');
  return [
    h2('Figure S2. Monte Carlo Distribution of Worst-Case Supply Reduction at Each γ Tier'),
    imgFromPath(imgPath, 6.5, 2.4),
    caption('Figure S2. Monte Carlo distribution of the four-pessimistic worst-case supply reduction at each γ tier, n = 500 draws per tier, seed 20260423. Red dashed line: mean; orange dotted lines: percentile-based 95 % CI. Tier 1 (γ = 1, additive-only): 82.59 % (95 % CI 76.59–87.83 %). Tier 2 (γ sampled from Table 1 uniform ranges): 87.93 % (95 % CI 83.03–91.93 %). Tier 3 (γ at Table 1 central values): 88.62 % (95 % CI 84.70–92.04 %). The same parameter draws are used across tiers for paired comparison; Tier 2 is wider than Tier 3 (8.90 vs 7.34 pp), reflecting the additional γ-sampling uncertainty propagated through the Monte Carlo. Source files: results/earth_future_revision/task2/figure_s2_tiered_mc.{pdf,png,svg}.'),
  ];
}

function figureS6() {
  const imgPath = path.join(REPO, 'results', 'earth_future_revision', 'task3', 'figure_s6_wsi_convention.png');
  return [
    h2('Figure S6. Alternative WSI-Convention Robustness'),
    imgFromPath(imgPath, 5.5, 5.5),
    caption('Figure S6. ΔWSI under the current WSI convention (renewable = natural sources + treated wastewater reuse; x-axis) versus the alternative convention (renewable = natural sources + desalination; y-axis) across the 243 Tier 3 compound scenarios. Point colour encodes the number of Pessimistic crises in the composition. Red dashed identity line. Spearman ρ = 0.970 (p < 10⁻¹⁵⁰) across the full ensemble, with 12 of the top-15 most severe scenarios common to both conventions. The scenario ranking is therefore robust to the WSI accounting choice, supporting the main-text claim that the headline findings do not hinge on the convention. Source files: results/earth_future_revision/task3/figure_s6_wsi_convention.{pdf,png,svg}.'),
  ];
}

function figureS7() {
  const imgPath = path.join(REPO, 'results', 'earth_future_revision', 'task5', 'figure_s7_response_threshold.png');
  return [
    h2('Figure S7. Response-Threshold ±20 % Sensitivity'),
    imgFromPath(imgPath, 7.5, 2.5),
    caption('Figure S7. Trigger frequency (% of 243 scenarios) for each of the four response categories under threshold perturbations at the deterministic Tier 3 configuration. Supply Expansion, Sustainability Measures, and Emergency Measures are each tested at −20 %, baseline, and +20 % of the Section 2.6 nominal threshold (Supply > 40 % reduction; ΔWSI > 0.5; gap worse than ensemble median). Resilience Hardening uses three severity-class bars (optimistic+, moderate+ baseline, pessimistic-only). Emergency Measures is the most threshold-sensitive (74.9 → 49.8 → 16.1 %); Sustainability Measures is nearly invariant (93.4 → 93.0 → 92.6 %). Category-level response assignment is therefore stable for Sustainability and Supply Expansion and materially threshold-dependent for Emergency and Resilience Hardening. Source files: results/earth_future_revision/task5/figure_s7_response_threshold.{pdf,png,svg}.'),
  ];
}

// Text S1–S3 — preserved from original, minor updates
function textS1() {
  return [
    h2('Text S1. Extended Hydrological Foundations'),
    para('Water systems function through interconnected physical, chemical, and operational processes that link water sources, treatment infrastructure, conveyance networks, and end-use demands. The hydrological foundation of compound crisis analysis rests on recognizing that these interconnections create pathways for stress propagation across system components. A crisis affecting one component — reduced precipitation, energy shortage, infrastructure damage, control system compromise — propagates through the system according to physical and operational dependencies rather than remaining isolated to its point of origin.'),
    para('Consider the hydrological water balance that governs any water supply system. Total supply S derives from the sum of available sources: natural freshwater, including surface water S_sw and groundwater S_gw, plus manufactured sources including desalination S_desal and treated wastewater for reuse S_reuse. Each source operates under distinct physical constraints and exhibits different vulnerability profiles. Surface water availability depends on precipitation P, evapotranspiration ET, and antecedent soil-moisture conditions through the rainfall-runoff relationship. Groundwater availability depends on aquifer recharge rates, storage depletion, and pumping capacity. Desalination depends on energy availability, membrane integrity, and control-system functionality. Reuse depends on wastewater collection, treatment capacity, and distribution infrastructure.'),
    para('Under compound crisis conditions, multiple sources experience simultaneous degradation. Drought reduces S_sw and S_gw through precipitation deficit and reduced recharge. Energy disruption reduces S_desal through constrained reverse-osmosis operations and potentially affects pumping capacity for all sources. Infrastructure damage reduces operational capacity across sources. The water stress index WSI = Demand / Renewable Supply consequently increases under compound conditions more rapidly than under single-crisis conditions, reflecting the multiplicative nature of supply degradation across sources.'),
    para('The framework captures these hydrological dynamics through source-specific impact functions that preserve the physical logic of water system operation. Drought affects only climate-dependent sources (surface water, groundwater) while leaving infrastructure-dependent sources (desalination, reuse) unaffected — assuming treatment facilities remain operational. Energy disruption primarily affects energy-intensive processes (desalination, pumping) while leaving gravity-fed or passive sources less affected. Conflict affects all physical infrastructure through potential damage. Cyber-attack affects digitally-controlled components (desalination SCADA, distribution management) while leaving manually-operated or isolated components functional. This source-specific treatment ensures that compound impacts emerge from the physical structure of water system dependencies rather than arbitrary modelling assumptions.'),
  ];
}

function textS2() {
  return [
    h2('Text S2. Framework Transferability'),
    para('The analytical framework is designed for re-parameterisation rather than direct transfer. Its essential components — crisis typology, severity parameterisation, compound construction, γ-tiered impact evaluation, Monte Carlo uncertainty propagation, retrospective grounding, and response mapping — are generic and can be instantiated for any water system with (i) identifiable supply components with distinct vulnerability profiles; (ii) quantifiable crisis impacts on supply or demand components; (iii) defined indicators for system-state assessment (analogous to WSI, DDR, gap); (iv) specifiable response categories relevant to the governance context.'),
    para('Application to other systems requires context-specific parameterisation. A groundwater-dependent system would weight drought parameters more heavily than a desalination-dependent coastal system. A system without significant cyber-physical infrastructure might exclude the cyber crisis type or weight it minimally. A system facing different geopolitical conditions would parameterise conflict differently. The framework structure remains constant while parameter values reflect system-specific characteristics.'),
    para('The main text (Section 4.4) identifies two system-class groups where the framework applies most directly: (a) desalination-dependent, energy-intensive, centrally-managed systems of comparable production scale — Singapore (NEWater/desalination-integrated), Malta, the United Arab Emirates (notably Abu Dhabi), Qatar, Kuwait, and Cyprus; and (b) highly engineered systems with different dominant hazard profiles where compound stress-testing still applies — the Netherlands (flood/drought compound exposure), south-east Spain and the Tagus–Segura transfer system (drought and infrastructure contestation), the California State Water Project (drought, energy, wildfire interaction), and Cape Town / Western Cape (drought and demand elasticity).'),
    para('Within each system, the specific severity parameterisations, interaction multipliers, and response thresholds must be re-derived from that system\'s data. The 243-scenario enumeration can be scaled up (more crisis types, finer severity gradations) or down (fewer types, binary severity) depending on analytical resources and decision-making needs. The framework contribution is the enumeration logic, the tiered γ uncertainty treatment, the retrospective-grounding protocol (as demonstrated for Israel in Section 3.2 and Table S8), and the response-mapping structure — not a library of ready-to-use parameter values.'),
  ];
}

function textS3() {
  const refs = [
    'AghaKouchak, A., Chiang, F., Huning, L.S., Love, C.A., Mallakpour, I., Mazdiyasni, O., Moftakhari, H., Papalexiou, S.M., Ragno, E., Sadegh, M., 2020. Climate extremes and compound hazards in a warming world. Annual Review of Earth and Planetary Sciences 48, 519–548.',
    'Bazilian, M., Rogner, H., Howells, M., Hermann, S., Arent, D., Gielen, D., Steduto, P., Mueller, A., Komor, P., Tol, R.S., Yumkella, K.K., 2011. Considering the energy, water and food nexus: Towards an integrated modelling approach. Energy Policy 39, 7896–7906.',
    'Booysen, M.J., Visser, M., Burger, R., 2019. Temporal case study of household behavioural response to Cape Town\'s Day Zero using meter data. Water Research 160, 414–420.',
    'Busby, J.W., Baker, K., Bazilian, M.D., Gilbert, A.Q., Grubert, E., Rai, V., Rhodes, J.D., Shidore, S., Smith, C.A., Webber, M.E., 2021. Cascading risks: Understanding the 2021 winter blackout in Texas. Energy Research and Social Science 77, 102106.',
    'Caretta, M.A., Mukherji, A., Arfanuzzaman, M., Betts, R.A., Gelfan, A., Hirabayashi, Y., et al., 2022. Water, in: Climate Change 2022: Impacts, Adaptation and Vulnerability. Cambridge University Press, Cambridge, pp. 551–712.',
    'CISA, 2024. Water and Wastewater Systems Sector: Sector Overview. U.S. Department of Homeland Security.',
    'Cook, B.I., Mankin, J.S., Anchukaitis, K.J., 2018. Climate change and drought: From past to future. Current Climate Change Reports 4, 164–179.',
    'Falkenmark, M., Lundqvist, J., Widstrand, C., 1989. Macro-scale water scarcity requires micro-scale approaches: Aspects of vulnerability in semi-arid development. Natural Resources Forum 13, 258–267.',
    'Flores, N.M., McBrien, H., Do, V., Kiang, M.V., Schlegelmilch, J., Casey, J.A., 2023. The 2021 Texas Power Crisis: distribution, duration, and disparities. Journal of Exposure Science & Environmental Epidemiology 33, 21–31.',
    'Gleick, P.H., 2014. Water, drought, climate change, and conflict in Syria. Weather, Climate, and Society 6, 331–340.',
    'Gleick, P.H., 2019. Water as a weapon and casualty of armed conflict. WIREs Water 6, e1351.',
    'Hassanzadeh, A., Rasekh, A., Galelli, S., Aghashahi, M., Taormina, R., Ostfeld, A., Banks, M.K., 2020. A review of cybersecurity incidents in the water sector. Journal of Environmental Engineering 146, 03120003.',
    'Leonard, M., Westra, S., Phatak, A., Lambert, M., van den Hurk, B., McInnes, K., Risbey, J., Schuster, S., Jakob, D., Stafford-Smith, M., 2014. A compound event framework for understanding extreme impacts. WIREs Climate Change 5, 113–128.',
    'Pascale, S., Kapnick, S.B., Delworth, T.L., Cooke, W.F., 2020. Increasing risk of another Cape Town Day Zero drought in the 21st century. Proceedings of the National Academy of Sciences 117, 29495–29503.',
    'Sadegh, M., Moftakhari, H., Gupta, H.V., Ragno, E., Mazdiyasni, O., Sanders, B., Matthew, R., AghaKouchak, A., 2018. Multihazard scenarios for analysis of compound extreme events. Geophysical Research Letters 45, 5470–5480.',
    'Shapira, N., Ayalon, O., Ostfeld, A., Farber, Y., Housh, M., 2021. Cybersecurity in water sector: Stakeholders perspective. Journal of Water Resources Planning and Management 147, 05021008.',
    'Spinoni, J., Vogt, J.V., Naumann, G., Barbosa, P., Dosio, A., 2018. Will drought events become more frequent and severe in Europe? International Journal of Climatology 38, 1718–1736.',
    'Tal, A., 2018. Addressing desalination\'s carbon footprint: The Israeli experience. Water 10, 197.',
    'Van Loon, A.F., Gleeson, T., Clark, J., Van Dijk, A.I., Stahl, K., Hannaford, J., et al., 2016. Drought in the Anthropocene. Nature Geoscience 9, 89–91.',
    'Zscheischler, J., Westra, S., van den Hurk, B.J., Seneviratne, S.I., Ward, P.J., Pitman, A., et al., 2018. Future climate risk from compound events. Nature Climate Change 8, 469–477.',
  ];
  return [
    h2('Text S3. Complete Reference List'),
    para('The following references are cited in the Supplementary Materials. For the full reference list of the main text, see the manuscript.'),
    ...refs.map(r => new Paragraph({
      children: [new TextRun({ text: r, size: 20 })],
      spacing: { after: 80 },
      indent: { left: 360, hanging: 360 },
    })),
  ];
}

// ----- assemble -----
const sections = [{
  properties: {
    page: {
      size: { width: 12240, height: 15840 },
      margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
    }
  },
  children: [
    ...titleBlock(),
    ...contentsBlock(),
    ...tableS1(),
    ...tableS2(),
    ...tableS3(),
    new Paragraph({ children: [new PageBreak()] }),
    ...tableS4(),
    new Paragraph({ children: [new PageBreak()] }),
    ...tableS5(),
    new Paragraph({ children: [new PageBreak()] }),
    ...tableS6(),
    new Paragraph({ children: [new PageBreak()] }),
    ...tableS7(),
    ...tableS8(),
    new Paragraph({ children: [new PageBreak()] }),
    ...figureS1(),
    new Paragraph({ children: [new PageBreak()] }),
    ...figureS2(),
    new Paragraph({ children: [new PageBreak()] }),
    ...figureS6(),
    new Paragraph({ children: [new PageBreak()] }),
    ...figureS7(),
    new Paragraph({ children: [new PageBreak()] }),
    ...textS1(),
    ...textS2(),
    ...textS3(),
  ],
}];

const doc = new Document({
  creator: 'Claude Code (multicrisis revision)',
  title: 'Supplementary Materials — Multicrisis Manuscript (Earth\'s Future revision)',
  description: 'Supplementary Materials accompanying the Earth\'s Future resubmission',
  styles: {
    default: { document: { run: { font: 'Arial', size: 22 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 32, bold: true, font: 'Arial' },
        paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 24, bold: true, font: 'Arial' },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 1 } },
    ]
  },
  sections,
});

Packer.toBuffer(doc).then(buffer => {
  const outPath = path.join(OUT_DIR, 'multicrisis_supplementary_FINAL.docx');
  const tmpPath = outPath + '.tmp';
  // Atomic write: write to temp file then rename, so if the process is
  // interrupted mid-write the destination path is never left at 0 bytes.
  fs.writeFileSync(tmpPath, buffer);
  fs.renameSync(tmpPath, outPath);
  const stat = fs.statSync(outPath);
  console.log(`Wrote ${outPath} (${stat.size} bytes)`);
}).catch(err => {
  console.error('Build failed:', err);
  process.exit(1);
});
