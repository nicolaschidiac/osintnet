import pytest
from osintnet.filings import extract_990

def example(extra=''):
    return f'''<Return xmlns="http://www.irs.gov/efile"><ReturnHeader><TaxYr>2023</TaxYr><Filer><EIN>123456789</EIN><BusinessName><BusinessNameLine1Txt>Example nonprofit</BusinessNameLine1Txt></BusinessName></Filer></ReturnHeader><ReturnData><IRS990><CYTotalRevenueAmt>100</CYTotalRevenueAmt><CYTotalExpensesAmt>80</CYTotalExpensesAmt><CYRevenuesLessExpensesAmt>20</CYRevenuesLessExpensesAmt><TotalFunctionalExpensesGrp><ProgramServicesAmt>70</ProgramServicesAmt><ManagementAndGeneralAmt>10</ManagementAndGeneralAmt><FundraisingAmt>0</FundraisingAmt></TotalFunctionalExpensesGrp>{extra}</IRS990><IRS990ScheduleO/></ReturnData></Return>'''.encode()

def test_identity_reconciliation_and_unknown_fields():
    data=extract_990(example())
    assert data['ein']=='123456789'and data['year']==2023
    assert data['discrepancies']==[]and data['advertising']is None
    assert data['schedules']==['IRS990ScheduleO']

def test_xml_entities_and_wrong_forms_refused():
    with pytest.raises(Exception):extract_990(b'<!DOCTYPE a [<!ENTITY e SYSTEM "file:///etc/passwd">]><a>&e;</a>')
    with pytest.raises(ValueError,match='form_990_required'):extract_990(b'<Return><ReturnHeader/><ReturnData><IRS990EZ/></ReturnData></Return>')

def test_discrepancy_is_explicit_not_adjusted():
    data=extract_990(example().replace(b'<CYRevenuesLessExpensesAmt>20',b'<CYRevenuesLessExpensesAmt>21'))
    assert data['surplus']==21 and data['discrepancies']==['revenue_less_expenses_does_not_match_reported_surplus']

def test_audit_and_accounting_disclosures_remain_distinct_from_proof():
    data=extract_990(example('<MethodOfAccountingCashInd>X</MethodOfAccountingCashInd><FSAuditedInd>false</FSAuditedInd><OtherExpensesGrp><Desc>CONSULTANT FEE</Desc><TotalAmt>100</TotalAmt><ProgramServicesAmt>100</ProgramServicesAmt></OtherExpensesGrp>'))
    assert data['schema_version']==2 and data['accounting_method_cash']=='X'
    assert data['financial_statements_audited']=='false'and data['independent_audit']is None
    assert data['other_expense_details'][0]['TotalAmt']=='100'
