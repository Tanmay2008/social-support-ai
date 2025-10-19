# 1_data_pipeline/synthetic_data_generator.py
import pandas as pd
import numpy as np
from faker import Faker
import json
from datetime import datetime, timedelta
import os
from typing import Dict, List, Any
import random

class SyntheticDataGenerator:
    def __init__(self, seed=42):
        self.fake = Faker()
        self.fake.seed_instance(seed)
        np.random.seed(seed)
        random.seed(seed)
        
    def generate_application_dataset(self, num_applicants: int = 100) -> pd.DataFrame:
        """Generate comprehensive application dataset"""
        applications = []
        
        for i in range(num_applicants):
            app_id = f"APP{1000 + i}"
            
            # Generate realistic applicant data
            application = {
                'application_id': app_id,
                'full_name': self.fake.name(),
                'email': self.fake.email(),
                'phone': self.fake.phone_number(),
                'address': self.fake.address().replace('\n', ', '),
                'date_of_birth': self.fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%Y-%m-%d'),
                'nationality': self.fake.country(),
                'marital_status': random.choice(['Single', 'Married', 'Divorced', 'Widowed']),
                'family_size': random.randint(1, 8),
                'dependents': random.randint(0, 5),
                'employment_status': random.choices(
                    ['Employed', 'Unemployed', 'Self-Employed', 'Student', 'Retired'],
                    weights=[0.4, 0.3, 0.15, 0.1, 0.05]
                )[0],
                'monthly_income': self._generate_income(),
                'income_source': random.choice(['Salary', 'Business', 'Investments', 'Pension', 'None']),
                'housing_type': random.choices(
                    ['Rented', 'Owned', 'Living with Family', 'Government Housing'],
                    weights=[0.5, 0.2, 0.2, 0.1]
                )[0],
                'monthly_rent': random.randint(0, 5000),
                'education_level': random.choices(
                    ['No Formal Education', 'Primary', 'Secondary', 'Diploma', 'Bachelor', 'Master', 'PhD'],
                    weights=[0.1, 0.15, 0.3, 0.2, 0.15, 0.08, 0.02]
                )[0],
                'support_type_requested': random.choice([
                    'Financial Aid', 'Housing Support', 'Education Support', 
                    'Healthcare Support', 'Employment Support'
                ]),
                'application_date': self.fake.date_this_year().strftime('%Y-%m-%d'),
                'emergency_contact': self.fake.name(),
                'emergency_phone': self.fake.phone_number()
            }
            
            applications.append(application)
        
        return pd.DataFrame(applications)
    
    def generate_bank_statements(self, application_ids: List[str]) -> List[Dict]:
        """Generate synthetic bank statement data"""
        bank_statements = []
        
        for app_id in application_ids:
            # Generate 3 months of bank statements
            for month in range(3):
                statement_date = (datetime.now() - timedelta(days=30*month)).strftime('%Y-%m-%d')
                
                # Realistic financial patterns
                if random.random() < 0.7:  # 70% have regular income
                    base_income = random.randint(2000, 8000)
                    expenses = random.randint(1500, 7000)
                else:  # 30% have irregular/low income
                    base_income = random.randint(500, 2000)
                    expenses = random.randint(800, 2500)
                
                opening_balance = random.randint(500, 15000)
                total_deposits = base_income + random.randint(-500, 1000)
                total_withdrawals = expenses + random.randint(-300, 500)
                closing_balance = opening_balance + total_deposits - total_withdrawals
                
                # Generate transaction details
                transactions = self._generate_transactions(total_deposits, total_withdrawals)
                
                bank_statement = {
                    'application_id': app_id,
                    'statement_date': statement_date,
                    'account_number': self.fake.bban(),
                    'account_type': random.choice(['Savings', 'Current', 'Salary']),
                    'bank_name': random.choice(['Emirates NBD', 'Mashreq Bank', 'ADCB', 'Dubai Islamic Bank']),
                    'opening_balance': opening_balance,
                    'total_deposits': total_deposits,
                    'total_withdrawals': total_withdrawals,
                    'closing_balance': closing_balance,
                    'transactions': transactions
                }
                bank_statements.append(bank_statement)
        
        return bank_statements
    
    def generate_credit_reports(self, application_ids: List[str]) -> List[Dict]:
        """Generate synthetic credit report data"""
        credit_reports = []
        
        for app_id in application_ids:
            # Credit score distribution
            credit_score = np.random.normal(650, 100)
            credit_score = max(300, min(850, int(credit_score)))
            
            # Determine credit rating
            if credit_score >= 800:
                credit_rating = 'Excellent'
            elif credit_score >= 740:
                credit_rating = 'Very Good'
            elif credit_score >= 670:
                credit_rating = 'Good'
            elif credit_score >= 580:
                credit_rating = 'Fair'
            else:
                credit_rating = 'Poor'
            
            # Generate credit accounts
            accounts = []
            num_accounts = random.randint(1, 8)
            
            for i in range(num_accounts):
                account_type = random.choice([
                    'Credit Card', 'Personal Loan', 'Mortgage', 'Auto Loan', 
                    'Student Loan', 'Line of Credit'
                ])
                
                account = {
                    'account_id': f"ACC{10000 + i}",
                    'type': account_type,
                    'lender': self.fake.company(),
                    'opening_date': self.fake.date_between(start_date='-10y', end_date='-1y').strftime('%Y-%m-%d'),
                    'current_balance': random.randint(0, 100000),
                    'credit_limit': random.randint(1000, 50000),
                    'payment_status': random.choices(
                        ['Current', '30 Days Late', '60 Days Late', '90+ Days Late', 'Paid Off'],
                        weights=[0.85, 0.08, 0.04, 0.02, 0.01]
                    )[0],
                    'monthly_payment': random.randint(50, 2000)
                }
                accounts.append(account)
            
            # Payment history (24 months)
            payment_history = []
            for month in range(24):
                status = random.choices(
                    ['On Time', '30 Days Late', '60 Days Late', '90+ Days Late'],
                    weights=[0.85, 0.08, 0.05, 0.02]
                )[0]
                payment_history.append(status)
            
            credit_report = {
                'application_id': app_id,
                'credit_score': credit_score,
                'credit_rating': credit_rating,
                'total_accounts': num_accounts,
                'total_debt': sum(acc['current_balance'] for acc in accounts),
                'available_credit': sum(acc['credit_limit'] for acc in accounts) - sum(acc['current_balance'] for acc in accounts),
                'credit_utilization': random.uniform(0.1, 0.8),
                'oldest_account_age': random.randint(1, 30),
                'recent_inquiries': random.randint(0, 5),
                'derogatory_marks': random.randint(0, 3),
                'accounts': accounts,
                'payment_history': payment_history,
                'report_date': datetime.now().strftime('%Y-%m-%d')
            }
            credit_reports.append(credit_report)
        
        return credit_reports
    
    def generate_assets_liabilities(self, application_ids: List[str]) -> List[Dict]:
        """Generate synthetic assets and liabilities data"""
        assets_data = []
        
        for app_id in application_ids:
            # Assets with realistic distributions
            assets = {
                'cash_savings': random.randint(0, 50000),
                'investment_accounts': random.randint(0, 100000),
                'real_estate_value': random.randint(0, 500000),
                'vehicle_value': random.randint(0, 50000),
                'retirement_accounts': random.randint(0, 200000),
                'other_assets': random.randint(0, 50000)
            }
            total_assets = sum(assets.values())
            
            # Liabilities correlated with assets
            liabilities = {
                'mortgage_debt': min(assets['real_estate_value'] * random.uniform(0, 0.8), 300000),
                'auto_loans': min(assets['vehicle_value'] * random.uniform(0, 1.2), 40000),
                'credit_card_debt': random.randint(0, 20000),
                'personal_loans': random.randint(0, 50000),
                'student_loans': random.randint(0, 100000),
                'other_debt': random.randint(0, 25000)
            }
            total_liabilities = sum(liabilities.values())
            
            net_worth = total_assets - total_liabilities
            
            asset_record = {
                'application_id': app_id,
                'total_assets': total_assets,
                'total_liabilities': total_liabilities,
                'net_worth': net_worth,
                'assets_breakdown': assets,
                'liabilities_breakdown': liabilities,
                'debt_to_income_ratio': round(total_liabilities / max(random.randint(2000, 10000), 1), 2),
                'update_date': datetime.now().strftime('%Y-%m-%d')
            }
            assets_data.append(asset_record)
        
        return assets_data
    
    def generate_employment_history(self, application_ids: List[str]) -> List[Dict]:
        """Generate synthetic employment history data"""
        employment_data = []
        
        for app_id in application_ids:
            employment_history = []
            num_jobs = random.randint(1, 4)
            
            for job_num in range(num_jobs):
                is_current = job_num == 0
                
                job = {
                    'employer': self.fake.company(),
                    'position': self.fake.job(),
                    'industry': random.choice([
                        'Technology', 'Healthcare', 'Education', 'Retail', 
                        'Manufacturing', 'Finance', 'Construction', 'Hospitality'
                    ]),
                    'start_date': self.fake.date_between(start_date='-10y', end_date='-6m').strftime('%Y-%m-%d'),
                    'end_date': 'Present' if is_current else self.fake.date_between(start_date='-5y', end_date='-1m').strftime('%Y-%m-%d'),
                    'employment_type': random.choice(['Full-time', 'Part-time', 'Contract', 'Temporary']),
                    'monthly_salary': random.randint(1000, 10000) if is_current else random.randint(800, 8000),
                    'reason_for_leaving': None if is_current else random.choice([
                        'Better opportunity', 'Company downsizing', 'Relocation', 'Career change'
                    ])
                }
                employment_history.append(job)
            
            employment_record = {
                'application_id': app_id,
                'total_experience_years': random.randint(1, 30),
                'current_employment_status': employment_history[0]['employment_type'],
                'current_industry': employment_history[0]['industry'],
                'employment_history': employment_history,
                'skills': random.sample([
                    'Communication', 'Problem Solving', 'Teamwork', 'Leadership',
                    'Technical Skills', 'Customer Service', 'Project Management',
                    'Data Analysis', 'Digital Literacy', 'Language Skills'
                ], random.randint(3, 8))
            }
            employment_data.append(employment_record)
        
        return employment_data
    
    def generate_training_opportunities(self) -> List[Dict]:
        """Generate synthetic training and upskilling opportunities"""
        training_programs = [
            {
                'program_id': 'TRN001',
                'name': 'Digital Literacy Fundamentals',
                'provider': 'National Skills Academy',
                'duration': '6 weeks',
                'format': 'Online',
                'cost': 'Free',
                'level': 'Beginner',
                'skills_covered': ['Computer Basics', 'Internet Skills', 'Email Communication', 'Online Safety'],
                'employment_rate': '85%',
                'prerequisites': 'None',
                'locations': ['Dubai', 'Abu Dhabi', 'Sharjah'],
                'next_intake': (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
            },
            {
                'program_id': 'TRN002',
                'name': 'Customer Service Professional',
                'provider': 'Service Excellence Institute',
                'duration': '8 weeks',
                'format': 'Hybrid',
                'cost': 'Subsidized',
                'level': 'Intermediate',
                'skills_covered': ['Customer Interaction', 'Problem Resolution', 'Communication Skills', 'CRM Software'],
                'employment_rate': '78%',
                'prerequisites': 'High School Diploma',
                'locations': ['Dubai', 'Abu Dhabi'],
                'next_intake': (datetime.now() + timedelta(days=21)).strftime('%Y-%m-%d')
            },
            {
                'program_id': 'TRN003',
                'name': 'Data Analysis Bootcamp',
                'provider': 'Tech Futures Foundation',
                'duration': '12 weeks',
                'format': 'Full-time',
                'cost': 'Scholarship Available',
                'level': 'Advanced',
                'skills_covered': ['Excel', 'SQL', 'Python', 'Data Visualization', 'Statistical Analysis'],
                'employment_rate': '92%',
                'prerequisites': 'Basic Math Skills',
                'locations': ['Dubai'],
                'next_intake': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            },
            {
                'program_id': 'TRN004',
                'name': 'Healthcare Assistant Certification',
                'provider': 'Medical Training Center',
                'duration': '10 weeks',
                'format': 'In-person',
                'cost': 'Government Funded',
                'level': 'Intermediate',
                'skills_covered': ['Patient Care', 'Medical Terminology', 'Vital Signs', 'Safety Procedures'],
                'employment_rate': '95%',
                'prerequisites': 'None',
                'locations': ['Abu Dhabi', 'Al Ain'],
                'next_intake': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            }
        ]
        
        return training_programs
    
    def generate_job_matches(self, application_ids: List[str]) -> List[Dict]:
        """Generate synthetic job matching data"""
        available_jobs = [
            {
                'job_id': 'JOB001',
                'title': 'Retail Sales Associate',
                'company': 'City Retail Group',
                'location': 'Dubai',
                'salary_range': '1800-2500 AED/month',
                'type': 'Full-time',
                'requirements': ['High School Diploma', 'Customer Service Skills', 'Communication Skills'],
                'description': 'Assist customers, manage inventory, process transactions',
                'industry': 'Retail',
                'experience_level': 'Entry'
            },
            {
                'job_id': 'JOB002',
                'title': 'Data Entry Specialist',
                'company': 'Admin Solutions LLC',
                'location': 'Business Bay, Dubai',
                'salary_range': '2200-3000 AED/month',
                'type': 'Full-time',
                'requirements': ['Typing Speed 40WPM', 'Attention to Detail', 'Basic Computer Skills'],
                'description': 'Enter and verify data, maintain records, generate reports',
                'industry': 'Administration',
                'experience_level': 'Entry'
            },
            {
                'job_id': 'JOB003',
                'title': 'Healthcare Assistant',
                'company': 'Community Medical Center',
                'location': 'Multiple Locations',
                'salary_range': '2500-3500 AED/month',
                'type': 'Full-time',
                'requirements': ['Training Provided', 'Compassionate Nature', 'Physical Stamina'],
                'description': 'Support medical staff, patient care, facility maintenance',
                'industry': 'Healthcare',
                'experience_level': 'Entry'
            }
        ]
        
        job_matches = []
        
        for app_id in application_ids:
            matched_jobs = random.sample(available_jobs, random.randint(1, 3))
            for job in matched_jobs:
                match_score = random.randint(60, 95)
                job_match = {
                    'application_id': app_id,
                    'job_id': job['job_id'],
                    'job_title': job['title'],
                    'company': job['company'],
                    'match_score': match_score,
                    'salary_range': job['salary_range'],
                    'match_reasons': random.sample([
                        'Skills alignment', 'Location proximity', 'Experience match', 
                        'Education requirements met', 'Industry experience'
                    ], random.randint(2, 4)),
                    'application_status': random.choice(['Recommended', 'High Match', 'Good Fit'])
                }
                job_matches.append(job_match)
        
        return job_matches
    
    def _generate_income(self) -> float:
        """Generate realistic income distribution"""
        # Bimodal distribution: some low income, some medium, few high
        choice = random.random()
        if choice < 0.4:  # 40% low income
            return random.randint(500, 2000)
        elif choice < 0.85:  # 45% medium income
            return random.randint(2000, 6000)
        else:  # 15% high income
            return random.randint(6000, 15000)
    
    def _generate_transactions(self, total_deposits: float, total_withdrawals: float) -> List[Dict]:
        """Generate realistic transaction data"""
        transactions = []
        
        # Generate deposits
        num_deposits = random.randint(1, 5)
        deposit_amounts = self._split_amount(total_deposits, num_deposits)
        
        for amount in deposit_amounts:
            transaction = {
                'date': self.fake.date_this_month().strftime('%Y-%m-%d'),
                'description': random.choice(['Salary', 'Business Income', 'Transfer', 'Investment Return']),
                'amount': amount,
                'type': 'credit',
                'balance': random.randint(1000, 20000)
            }
            transactions.append(transaction)
        
        # Generate withdrawals
        num_withdrawals = random.randint(8, 20)
        withdrawal_amounts = self._split_amount(total_withdrawals, num_withdrawals)
        
        for amount in withdrawal_amounts:
            transaction = {
                'date': self.fake.date_this_month().strftime('%Y-%m-%d'),
                'description': random.choice([
                    'Rent Payment', 'Groceries', 'Utility Bill', 'Transportation',
                    'Healthcare', 'Education', 'Entertainment', 'Shopping'
                ]),
                'amount': -amount,
                'type': 'debit',
                'balance': random.randint(500, 15000)
            }
            transactions.append(transaction)
        
        # Sort by date
        transactions.sort(key=lambda x: x['date'])
        return transactions
    
    def _split_amount(self, total: float, num_parts: int) -> List[float]:
        """Split amount into random parts that sum to total"""
        parts = [random.random() for _ in range(num_parts)]
        total_parts = sum(parts)
        return [round((p / total_parts) * total, 2) for p in parts]
    
    def generate_complete_dataset(self, num_applicants: int = 50, output_dir: str = "data/output"):
        """Generate complete synthetic dataset"""
        os.makedirs(output_dir, exist_ok=True)
        
        print("Generating synthetic data for social support application prototype...")
        
        # Generate core datasets
        applications_df = self.generate_application_dataset(num_applicants)
        application_ids = applications_df['application_id'].tolist()
        
        bank_statements = self.generate_bank_statements(application_ids)
        credit_reports = self.generate_credit_reports(application_ids)
        assets_data = self.generate_assets_liabilities(application_ids)
        employment_data = self.generate_employment_history(application_ids)
        training_opportunities = self.generate_training_opportunities()
        job_matches = self.generate_job_matches(application_ids)
        
        # Save datasets
        applications_df.to_csv(f'{output_dir}/applications.csv', index=False)
        
        with open(f'{output_dir}/bank_statements.json', 'w') as f:
            json.dump(bank_statements, f, indent=2)
        
        with open(f'{output_dir}/credit_reports.json', 'w') as f:
            json.dump(credit_reports, f, indent=2)
        
        with open(f'{output_dir}/assets_liabilities.json', 'w') as f:
            json.dump(assets_data, f, indent=2)
        
        with open(f'{output_dir}/employment_history.json', 'w') as f:
            json.dump(employment_data, f, indent=2)
        
        with open(f'{output_dir}/training_opportunities.json', 'w') as f:
            json.dump(training_opportunities, f, indent=2)
        
        with open(f'{output_dir}/job_matches.json', 'w') as f:
            json.dump(job_matches, f, indent=2)
        
        # Generate sample document texts (for OCR simulation)
        self.generate_sample_documents(application_ids, output_dir)
        
        print(f"✅ Generated synthetic data for {num_applicants} applicants")
        print(f"📁 Files created in {output_dir}/ directory")
        
        return {
            'applications': applications_df,
            'bank_statements': bank_statements,
            'credit_reports': credit_reports,
            'assets_data': assets_data,
            'employment_data': employment_data,
            'training_opportunities': training_opportunities,
            'job_matches': job_matches
        }
    
    def generate_sample_documents(self, application_ids: List[str], output_dir: str):
        """Generate sample document text for OCR simulation"""
        documents = []
        
        for app_id in application_ids:
            # Sample application form text
            app_form = {
                'application_id': app_id,
                'document_type': 'application_form',
                'extracted_text': f"""
                SOCIAL SUPPORT APPLICATION FORM
                
                Application ID: {app_id}
                Full Name: {self.fake.name()}
                Date of Birth: {self.fake.date_of_birth().strftime('%Y-%m-%d')}
                National ID: {self.fake.random_number(digits=12)}
                Address: {self.fake.address().replace('\n', ', ')}
                
                FAMILY INFORMATION:
                Marital Status: {random.choice(['Single', 'Married', 'Divorced'])}
                Number of Dependents: {random.randint(0, 5)}
                Total Family Members: {random.randint(1, 7)}
                
                INCOME INFORMATION:
                Employment Status: {random.choice(['Employed', 'Unemployed', 'Self-Employed'])}
                Monthly Income: {random.randint(500, 5000)} AED
                Income Source: {random.choice(['Salary', 'Business', 'Investments'])}
                
                SUPPORT REQUESTED:
                Type: {random.choice(['Financial Aid', 'Housing Support', 'Education Support'])}
                Amount Requested: {random.randint(1000, 10000)} AED
                Reason: {random.choice(['Job Loss', 'Medical Emergency', 'Family Crisis', 'Educational Needs'])}
                
                DECLARATION:
                I hereby declare that the information provided is true and accurate.
                Signature: ___________________
                Date: {datetime.now().strftime('%Y-%m-%d')}
                """
            }
            documents.append(app_form)
            
            # Sample bank statement text
            bank_stmt = {
                'application_id': app_id,
                'document_type': 'bank_statement',
                'extracted_text': f"""
                NATIONAL BANK OF UAE
                BANK STATEMENT
                
                Account Holder: {self.fake.name()}
                Account Number: {self.fake.bban()}
                Statement Period: {self.fake.date_between(start_date='-30d', end_date='today').strftime('%Y-%m-%d')}
                
                Opening Balance: {random.randint(1000, 5000)} AED
                Closing Balance: {random.randint(500, 8000)} AED
                
                TRANSACTIONS:
                Date: {self.fake.date_this_month().strftime('%Y-%m-%d')} | Description: Salary Credit | Amount: +{random.randint(2000, 8000)} AED
                Date: {self.fake.date_this_month().strftime('%Y-%m-%d')} | Description: Rent Payment | Amount: -{random.randint(1000, 3000)} AED
                Date: {self.fake.date_this_month().strftime('%Y-%m-%d')} | Description: Groceries | Amount: -{random.randint(200, 800)} AED
                Date: {self.fake.date_this_month().strftime('%Y-%m-%d')} | Description: Utility Bills | Amount: -{random.randint(100, 500)} AED
                
                Total Deposits: {random.randint(2000, 10000)} AED
                Total Withdrawals: {random.randint(1500, 9000)} AED
                """
            }
            documents.append(bank_stmt)
        
        with open(f'{output_dir}/sample_documents.json', 'w') as f:
            json.dump(documents, f, indent=2)

# Example usage
if __name__ == "__main__":
    generator = SyntheticDataGenerator()
    all_data = generator.generate_complete_dataset(num_applicants=50)