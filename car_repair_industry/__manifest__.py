# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    "name": "Car Customization and Service Repair Management",
    "version": "18.0.0.0",
    "depends": ['base', 'sale', 'purchase', 'account', 'sale_stock', 'mail', 'product', 'stock', 'fleet','sale_management', 'website', 'calendar', 'hr_timesheet','web'],
    "author": "ADX",
    "summary": "Car Customization and Service Repair Management",
    "description": """
    - Car Customization
    - Service Repair Management
    """,
    'category': 'Industries',
    'price': 129,
    'currency': "EUR",
    "website": "adx",
    "data": [
        'security/fleet_repair_security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/mail_template_data.xml',
        'wizard/fleet_repair_assign_to_head_tech_view.xml',
        'wizard/fleet_diagnose_assign_to_technician_view.xml',
        'wizard/pause_wizard.xml',
        'views/fleet_repair_view.xml',
        'views/fleet_repair_service_checklist_view.xml',
        'views/fleet_repair_sequence.xml',
        'views/fleet_diagnose_view.xml',
        'views/fleet_workorder_sequence.xml',
        'views/fleet_workorder_view.xml',
        'views/custom_sale_view.xml',
        'views/calendar_event_view.xml',
        'views/appointment_slots_views.xml',
        'views/configration.xml',
        'views/dashboard.xml',
        'views/templates.xml',
        'report/fleet_repair_label_view.xml',
        'report/fleet_repair_label_menu.xml',
        'report/fleet_repair_receipt_view.xml',
        'report/fleet_repair_receipt_menu.xml',
        'report/fleet_repair_checklist_view.xml',
        'report/fleet_repair_checklist_menu.xml',
        'report/fleet_diagnostic_request_report_view.xml',
        'report/fleet_diagnostic_request_report_menu.xml',
        'report/fleet_diagnostic_result_report_view.xml',
        'report/fleet_diagnostic_result_report_menu.xml',
        'report/fleet_workorder_report_view.xml',
        'report/fleet_workorder_report_menu.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'car_repair_industry/static/src/css/custom.css',
            'car_repair_industry/static/src/js/slot_time.js',
        ],
        'web.assets_backend': [
            'car_repair_industry/static/src/js/fleet_repair_dashboard.js',
            'car_repair_industry/static/src/xml/**/*',
        ],
    },
    'qweb': [
    ],
    "auto_install": False,
    "installable": True,
    'live_test_url': 'adixat.com',
    "images": ['static/description/Banner.gif'],
    "license": 'OPL-1',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
