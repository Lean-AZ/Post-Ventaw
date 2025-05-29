from odoo import api, SUPERUSER_ID

def create_no_fiscal_journal(env):
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
                'type': 'general',
                'company_id': company.id,
            })

def create_advance_account(env):
    # Get all companies
    companies = env['res.company'].search([])
    
    for company in companies:
        # Check if the advance account already exists for this company
        existing_account = env['account.account'].search([
            ('name', '=', 'Avance recibido de clientes'),
            ('company_id', '=', company.id)
        ], limit=1)
        
        if not existing_account:
            # Get the receivable account type
            account_type = env['account.account.type'].search([('type', '=', 'asset_receivable')], limit=1)
            
            if account_type:
                # Create the advance account if it doesn't exist for this company
                env['account.account'].create({
                    'name': 'Avance recibido de clientes',
                    'code': '430000',  # Using a standard code for customer advances
                    'company_id': company.id,
                    'user_type_id': account_type.id,
                    'reconcile': True,
                })

def create_late_payment_income_account(env):
    # Get all companies
    companies = env['res.company'].search([])
    
    for company in companies:
        # Check if the late payment income account already exists for this company
        existing_account = env['account.account'].search([
            ('name', '=', 'Ingresos por Mora e intereses clientes'),
            ('company_id', '=', company.id)
        ], limit=1)
        
        if not existing_account:
            # Get the income account type
            account_type = env['account.account.type'].search([('type', '=', 'income')], limit=1)
            
            if account_type:
                # Create the late payment income account if it doesn't exist for this company
                env['account.account'].create({
                    'name': 'Ingresos por Mora e intereses clientes',
                    'code': '760000',  # Using a standard code for other income
                    'company_id': company.id,
                    'user_type_id': account_type.id,
                    'reconcile': False,
                })

def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    create_no_fiscal_journal(env)
    create_advance_account(env)
    create_late_payment_income_account(env) 