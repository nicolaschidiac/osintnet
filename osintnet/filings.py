"""Extract named IRS XML fields without silently inventing absent amounts."""
import re
from defusedxml import ElementTree as ET

AMOUNTS={'revenue':'CYTotalRevenueAmt','expenses':'CYTotalExpensesAmt','net_assets':'NetAssetsOrFundBalancesEOYAmt','net_assets_begin':'NetAssetsOrFundBalancesBOYAmt','surplus':'CYRevenuesLessExpensesAmt','program_expenses':'TotalFunctionalExpensesGrp/ProgramServicesAmt','management_expenses':'TotalFunctionalExpensesGrp/ManagementAndGeneralAmt','fundraising_expenses':'TotalFunctionalExpensesGrp/FundraisingAmt','advertising':'AdvertisingGrp/TotalAmt','advertising_program':'AdvertisingGrp/ProgramServicesAmt','government_grants':'GovernmentGrantsAmt','foreign_grants':'ForeignGrantsGrp/TotalAmt','assets':'TotalAssetsGrp/EOYAmt','liabilities':'TotalLiabilitiesGrp/EOYAmt'}

def extract_990(raw):
    if len(raw)>8_000_000:raise ValueError('xml_size_limit')
    root=ET.fromstring(raw);namespace=root.tag.split('}')[0][1:]if'}'in root.tag else''
    def path(expression):return '/'.join('{'+namespace+'}'+part for part in expression.split('/'))
    header=root.find(path('ReturnHeader'));data=root.find(path('ReturnData'));form=data.find(path('IRS990'))if data is not None else None
    if header is None or form is None:raise ValueError('form_990_required')
    def text(parent,expression):
        elem=parent.find(path(expression));return elem.text.strip()if elem is not None and elem.text else None
    ein=text(header,'Filer/EIN');year=text(header,'TaxYr')
    if not ein or not re.fullmatch(r'\d{9}',ein)or not year or not re.fullmatch(r'\d{4}',year):raise ValueError('filing_identity_missing')
    fields={}
    for name,location in AMOUNTS.items():
        value=text(form,location)
        if value is not None and not re.fullmatch(r'-?\d+',value):raise ValueError('invalid_amount')
        fields[name]=int(value)if value is not None else None
    officers=[]
    for group in form.findall(path('Form990PartVIISectionAGrp')):
        officers.append({'name':text(group,'PersonNm'),'title':text(group,'TitleTxt'),'organization_compensation':text(group,'ReportableCompFromOrgAmt'),'related_organization_compensation':text(group,'ReportableCompFromRltdOrgAmt'),'other_compensation':text(group,'OtherCompensationAmt')})
    details=[]
    for group in form.findall(path('OtherExpensesGrp')):
        details.append({'description':text(group,'Desc'),**{k:text(group,k)for k in ('TotalAmt','ProgramServicesAmt','ManagementAndGeneralAmt','FundraisingAmt')}})
    review={'financial_statements_audited':text(form,'FSAuditedInd'),'independent_audit':text(form,'IndependentAuditFinclStmtInd'),'accountant_compile_or_review':text(form,'AccountantCompileOrReviewInd'),'professional_fundraising':text(form,'ProfessionalFundraisingInd'),'foreign_office':text(form,'ForeignOfficeInd'),'related_organization_control':text(form,'RelatedOrganizationCtrlEntInd'),'other_changes_in_net_assets':text(form,'OtherChangesInNetAssetsAmt'),'fundraising_event_contributions':text(form,'ContriRptFundraisingEventAmt'),'other_expense_details':details,'listed_contractor_groups':len(form.findall(path('Form990PartVIISectionBGrp')))}
    discrepancies=[]
    if all(fields[k]is not None for k in('revenue','expenses','surplus'))and fields['revenue']-fields['expenses']!=fields['surplus']:discrepancies.append('revenue_less_expenses_does_not_match_reported_surplus')
    if all(fields[k]is not None for k in('assets','liabilities','net_assets'))and fields['assets']-fields['liabilities']!=fields['net_assets']:discrepancies.append('assets_less_liabilities_does_not_match_net_assets')
    if all(fields[k]is not None for k in('program_expenses','management_expenses','fundraising_expenses','expenses'))and sum(fields[k]for k in('program_expenses','management_expenses','fundraising_expenses'))!=fields['expenses']:discrepancies.append('functional_classifications_do_not_sum_to_total_expenses')
    return {'schema_version':2,'is_primary':True,'ein':ein,'year':int(year),'name':text(header,'Filer/BusinessName/BusinessNameLine1Txt'),'tax_period_begin':text(header,'TaxPeriodBeginDt'),'tax_period_end':text(header,'TaxPeriodEndDt'),'submitted':text(header,'ReturnTs'),'mission':text(form,'MissionDesc'),'accounting_method_cash':text(form,'MethodOfAccountingCashInd'),'accounting_method_accrual':text(form,'MethodOfAccountingAccrualInd'),'foreign_activities_reported':text(form,'ForeignActivitiesInd'),'schedules':[child.tag.rsplit('}',1)[-1]for child in data if child.tag.rsplit('}',1)[-1]!='IRS990'],'officers':officers,'fields':AMOUNTS,'discrepancies':discrepancies,**review,**fields}
