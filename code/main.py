"""
Main entry point for Multi-Domain Support Triage Agent.

Reads support_tickets.csv, processes each ticket through the full pipeline,
and writes structured output to output.csv.
"""

import csv
import os
from tqdm import tqdm
from agent import process_ticket
from config import INPUT_CSV, OUTPUT_CSV


def read_tickets(filepath: str) -> list[dict]:
    """
    Read support tickets from CSV file.
    
    Args:
        filepath: Path to input CSV file
        
    Returns:
        List of ticket dictionaries
    """
    tickets = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tickets.append(row)
    
    return tickets


def write_output(filepath: str, results: list[dict]):
    """
    Write results to output CSV file.
    
    Args:
        filepath: Path to output CSV file
        results: List of result dictionaries
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    fieldnames = ['issue', 'subject', 'company', 'response', 'product_area', 'status', 'request_type', 'justification']
    
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def main():
    """
    Main execution function.
    
    Processes all tickets and writes output.
    """
    print("=" * 80)
    print("MULTI-DOMAIN SUPPORT TRIAGE AGENT")
    print("=" * 80)
    print()
    
    # Check if input file exists
    if not os.path.exists(INPUT_CSV):
        print(f"Error: Input file not found: {INPUT_CSV}")
        print("Please ensure support_tickets.csv exists at the specified path.")
        return
    
    # Read tickets
    print(f"Reading tickets from: {INPUT_CSV}")
    tickets = read_tickets(INPUT_CSV)
    print(f"Loaded {len(tickets)} tickets")
    print()
    
    # Process tickets
    results = []
    
    for i, ticket in enumerate(tqdm(tickets, desc="Processing tickets"), 1):
        issue = ticket.get('Issue', ticket.get('issue', ''))
        subject = ticket.get('Subject', ticket.get('subject', ''))
        company = ticket.get('Company', ticket.get('company', ''))
        
        try:
            # Process ticket through pipeline
            output = process_ticket(issue, subject, company)
            
            # Build result row
            result = {
                'issue': issue,
                'subject': subject,
                'company': company,
                'response': output.response,
                'product_area': output.product_area,
                'status': output.status,
                'request_type': output.request_type,
                'justification': output.justification
            }
            
            results.append(result)
            
            # Log result
            company_display = company if company and company.lower() != 'none' else 'global'
            print(f"[TICKET {i:02d}/{len(tickets):02d}] {output.status:9s} — domain: {company_display:12s} — type: {output.request_type}")
        
        except Exception as e:
            # Handle errors gracefully - create escalated row
            print(f"[TICKET {i:02d}/{len(tickets):02d}] ERROR — {str(e)}")
            
            result = {
                'issue': issue,
                'subject': subject,
                'company': company,
                'response': 'An error occurred while processing your request. Escalating to a human agent.',
                'product_area': 'General Support',
                'status': 'escalated',
                'request_type': 'product_issue',
                'justification': f'Processing error: {str(e)}'
            }
            
            results.append(result)
    
    # Write output
    print()
    print(f"Writing results to: {OUTPUT_CSV}")
    write_output(OUTPUT_CSV, results)
    
    # Summary statistics
    print()
    print("=" * 80)
    print("PROCESSING COMPLETE")
    print("=" * 80)
    print(f"Total tickets processed: {len(results)}")
    print(f"Replied: {sum(1 for r in results if r['status'] == 'replied')}")
    print(f"Escalated: {sum(1 for r in results if r['status'] == 'escalated')}")
    print()
    print(f"Output saved to: {OUTPUT_CSV}")
    print("=" * 80)


if __name__ == "__main__":
    main()
