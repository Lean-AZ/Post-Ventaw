from odoo import api, SUPERUSER_ID

def _create_no_fiscal_journal(env):
    # Get all companies
    companies = env['res.company'].search([])
    
    for company in companies:
        # Check if a journal with 'no fiscal' in the name already exists for this company
        existing_journal = env['account.journal'].search([
            ('name', 'ilike', 'no fiscal'),
            ('company_id', '=', company.id)
        ], limit=1)
        
        if not existing_journal:
            # Create the journal if it doesn't exist for this company
            env['account.journal'].create({
                'name': 'No Fiscal Journal',
                'code': 'NFJ',
                'type': 'sale',
                'company_id': company.id,
            })

def _create_advance_account(env):
    # Get all companies
    companies = env['res.company'].search([])
    
    for company in companies:
        # Check if the advance account already exists for this company
        existing_account = env['account.account'].search([
            ('name', '=', 'Avance recibido de clientes'),
            ('company_id', '=', company.id)
        ], limit=1)
        
        if not existing_account:
            # Create the advance account if it doesn't exist for this company
            env['account.account'].create({
                'name': 'Avance recibido de clientes',
                'code': '430000',  # Using a standard code for customer advances
                'company_id': company.id,
                'account_type': 'liability_non_current',
                'reconcile': True,
            })

def _create_late_payment_income_account(env):
    # Get all companies
    companies = env['res.company'].search([])
    
    for company in companies:
        # Check if the late payment income account already exists for this company
        existing_account = env['account.account'].search([
            ('name', '=', 'Ingresos por Mora e intereses clientes'),
            ('company_id', '=', company.id)
        ], limit=1)
        
        if not existing_account:
            # Create the late payment income account if it doesn't exist for this company
            env['account.account'].create({
                'name': 'Ingresos por Mora e intereses clientes',
                'code': '760000',  # Using a standard code for other income
                'company_id': company.id,
                'account_type': 'income_other',
                'reconcile': False,
            })

def post_init_hook(env):
    _create_no_fiscal_journal(env)
    _create_advance_account(env)
    _create_late_payment_income_account(env) 

