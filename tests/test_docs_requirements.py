import re
from pathlib import Path

def test_requirements_unique_acceptance():
    txt=Path('docs/requirements/WP_02_requirements.md').read_text()
    ids=re.findall(r'\| ((?:BUS|SCI|FUN|PERF|OPS|SEC|INT|DATA|VAL|DOC)-\d{3}) ', txt)
    assert ids and len(ids)==len(set(ids))
    assert 'Acceptance criterion' in txt

def test_reports_sections_and_no_placeholders():
    for p in ['docs/reports/WP_02_Needs_and_Feasibility_Study.md','docs/reports/MAJA_Improvement_Audit.md']:
        txt=Path(p).read_text(encoding='utf-8')
        assert len(txt)>1000 and 'TODO' not in txt and 'TBD' not in txt and 'INSERT IMAGE' not in txt

def test_stakeholder_status():
    txt=Path('docs/requirements/WP_02_stakeholder_validation.md').read_text()
    assert 'Draft' in txt and 'Approved' in txt and 'Aucune approbation' in txt
